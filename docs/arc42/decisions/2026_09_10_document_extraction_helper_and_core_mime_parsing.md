# Document Extraction Helper and MIME Parsing in `packages/core`

## Context

An inbound document-management integration (M-Files) posts files into the platform as raw content — PDFs, scans, Office
documents and `.eml` mail — rather than as pre-extracted text. Before any of it can be classified, every file has to
become a **title and a body**, whatever its format and whichever loader handles it.

Most of the machinery already existed. `DocumentLoaderSelector` routes an extension to a loader,
`S3AnonymousFileAccessService.download_file` reads bytes from a bucket, and every loader shares one
`aload_data_from_bytes` signature. Three things did not exist:

1. No single call went from an S3 object to a title and a body.
2. **No title derivation existed anywhere.** Every `document_title` in the platform is the last path segment of the
   source URI, so `2f8c-invoice-final-v2.pdf` is the "title" of that document.
3. **`.eml` had no usable extraction.** `MarkItDownLoader` claims the extension, but measuring what it returns showed it
   emits the **raw RFC822 source** — MIME boundaries, transfer-encoding headers, unconverted HTML and base64 attachment
   payloads. Not markdown, and with no separation between subject and body.

The correct MIME parser did exist — `MailParser`, built for the IMAP agent — but it lived in `packages/agent` and
returned plain text rather than markdown.

## Decision Drivers

- **One output contract.** Every loader returns markdown. A file type that returned something else would push the
  difference onto every consumer, starting with the classifier's prompt.
- **Routing must stay in one place.** The routing table is already stated three times (the selector, the ingestion
  pipeline, the API's parsing endpoint). A fourth copy, or a per-format branch inside the new helper, makes it worse.
- **Base64 must not reach a prompt.** An attachment payload inlined into extracted text spends the model's context
  window on nothing and is the concrete failure of the existing `.eml` path.
- **One MIME parser.** Mail arriving as a file and mail arriving over IMAP are the same parsing problem.
- **Transport-agnostic.** Extraction must not care whether bytes came from a webhook, a knowledge upload or an agent
  attachment.

## Decision

**A `DocumentExtractor` in `packages/core`** (`generative_ai/document/extraction/`) taking an explicit **bucket and
key** — with an `s3://` convenience and a bytes entry point — and returning an `ExtractedDocument` carrying title,
content, content type, source filename, `document_parser`, page count and source. It holds **no per-format branch**:
routing is delegated wholesale to `DocumentLoaderSelector`.

**`document_parser` is recorded on the result**, following the existing `parse_document_from_data_lake` convention.
Without it there is no way to assert which loader ran: both `MineruLoader` and `MarkItDownLoader` emit
`number_of_pages`, so that field cannot distinguish them.

**Unsupported types raise** `UnsupportedDocumentTypeError` rather than returning empty. The selector's `None` is right
for its callers; a helper whose contract is "give me a title and a body" has no empty result to return. A `can_extract`
predicate lets a caller holding only a reference skip a file **before** paying to fetch its bytes.

**A new `EmlLoader` composes `MailParser` with `MarkItDownLoader`**: the parser does the MIME work (subject, decoded
body parts, attachment names) and an HTML-only body is converted by MarkItDown, whose standalone-HTML conversion is
good. It renders the subject as an H1, lists attachment **filenames**, and never their bytes — `MailParser` is asked to
discard attachment payloads, and the names are read off the message parts separately. That bounds what is *retained*,
not what is decoded: `MailParser` decodes a payload before comparing its size, so a large attachment is still
materialised once and thrown away. Moving the check ahead of the decode would change parsing for the IMAP agent too, so
it is recorded as a follow-up rather than done here.

**`EmlLoader` is registered in `DocumentLoaderSelector` ahead of `MarkItDownLoader`**, so `.eml` is *routed* like every
other type rather than special-cased in the extractor. `.msg` (Outlook's binary format, which the stdlib `email` module
cannot read) stays with MarkItDown.

**`MailParser`, `ParsedMessage` and `ParsedAttachment` move to `packages/core/imap/`**, because `EmlLoader` lives in
core and the alternative was a second MIME parser inside the document layer. `MAX_SUBJECT_CHARACTERS` moves with the
parser that enforces it.

**Title derivation is a fallback chain** — email subject, then the first markdown heading (any level, since MinerU
labels a scan's title by visual prominence), then the filename stem.

## Consequences

- **`AttachmentTextExtractor` is the second consumer**, so the helper is reused by more than one feature — a real
  existing one, rather than a consumer written to satisfy that requirement. Its bounds and outcome semantics are
  unchanged, including that an unreadable type still costs no S3 fetch.
- **A shipped behaviour changes**: an `.eml` attachment reaching the IMAP drafting path stops being a raw MIME dump and
  becomes clean markdown with a subject heading. This is a latent-bug fix, but it changes what that feature sees and
  must be reviewed as such. **It applies only to an `.eml` attached as a generic binary part.** Measured against a real
  mailbox: a part with `Content-Type: message/rfc822` — which is how Python's `add_attachment` and many mail clients
  attach forwarded mail — reports `is_multipart() == True`, so `MailParser.parse_message` skips it and the attachment
  never reaches a loader at all. That is pre-existing behaviour, unchanged here and out of scope; it is filed as a
  follow-up. The same file attached as `application/octet-stream` does reach `EmlLoader`.
- **`MarkItDownLoader.SUPPORTED_EXTENSIONS` still lists `eml`**, deliberately: the ingestion pipeline and the API's
  parsing endpoint build their own maps from that list and are out of scope here. Only the chain order in the selector
  keeps mail off MarkItDown, so that ordering is pinned by a test.
- **`MailParser` decodes an attachment payload before checking its size**, so parsing an `.eml` carrying a large
  attachment costs that much transient memory even though the bytes are discarded immediately.
- **`message/rfc822` attachments are invisible to `MailParser`** (see above) — worth fixing, but it is a change to mail
  parsing rather than to extraction, and it would alter what the IMAP agent considers an attachment.
- **`.eml` uploaded to a knowledge base is still stored as raw MIME and base64**, because `DocumentParserResource` keeps
  its own loader map. Filed as a follow-up; fixing it changes ingestion behaviour and would require re-ingesting
  existing `.eml` documents.
- **A new import edge** runs `generative_ai` → `core.imap`, while `core.imap.draft_email_settings` already imports
  `generative_ai...llm_config`. No cycle forms, because both package `__init__.py`s are lazy and `EmlLoader` imports the
  concrete module rather than the package. All three properties are easy to undo by accident and breaking any one breaks
  `import swiss_ai_hub.core.generative_ai` for every consumer, so a test imports both packages in either order in a
  clean interpreter.
- **No new dependency**: `.eml` uses the standard-library `email` module.
