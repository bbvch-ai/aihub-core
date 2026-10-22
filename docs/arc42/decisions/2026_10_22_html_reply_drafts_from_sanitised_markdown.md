# Reply Drafts Are HTML Rendered from Markdown and Sanitised with nh3

## Context

The mailbox agents (`ImapAgent`, `EmailClassificationAgent`) left every reply draft as a single `text/plain` part. Two
customer requests needed more than that:

- aihub-core-private#368: formatting in the draft, above all highlighting a sentence in yellow so the reviewer sees it.
  HTML the model wrote showed up as literal tags.
- aihub-core-private#369: the original email quoted below the reply, the way a reply in Outlook does, with a header block
  and the original's own HTML body.

Both put untrusted HTML into a message that a person opens in their mail client. The quoted original is written by the
sender. The reply is written by a model that read the sender's mail. Neither can be trusted, and the platform had no
HTML sanitiser at all: `ParsedMessage.body_html` was documented as "must be sanitised before use" and nothing used it.

## Decision Drivers

- Formatting has to render in Outlook desktop, which uses Word's HTML engine and ignores `<mark>` and most CSS.
- Nothing in model output or the quoted original may carry script, event handlers, forms or images into the draft.
  Remote images are tracking pixels fetched when the reviewer opens the draft.
- The model should not be asked to write HTML. Models write Markdown unprompted, and the knowledge agent's answers that
  grounded drafts are made from are already Markdown.
- Quoting must not change what the model sees or writes.

## Decision

- **Markdown in, HTML out.** `DraftBodyRenderer` renders the model's body with `markdown-it-py` (CommonMark plus
  tables). Raw HTML in the output is passed to the sanitiser rather than escaped, because a prompt that asks for
  highlighting often gets a `<span style=...>` back. `==text==` is the highlight syntax the default prompt offers. It is
  turned into `<mark>`, and after sanitising into `<span style="background-color:#ffff00">`, which Outlook renders.
- **nh3 is the sanitiser.** `MailHtmlSanitizer` holds two allowlists: a narrow one for the reply (text formatting,
  lists, tables, links, `background-color`/`color` styles) and a wider one for the quoted original that keeps its layout
  (tables, fonts, spacing CSS). Neither allows `img`. `script`, `style`, `title` and `head` lose their content. Links
  are restricted to `http`, `https` and `mailto`.
- **Every draft is `multipart/alternative`.** The plain-text part is the Markdown as written, minus highlight markers
  and tags. Clients that do not render HTML still get a readable draft.
- **Quoting is a toggle** (`DraftEmailSettings.quote_original`, off by default). `QuotedOriginal` builds the separator,
  a From/Sent/To/Cc/Subject block in the run's locale (labels and date format in `lib.imap.quote.*`) and the sanitised
  original, or its text body escaped when it has no HTML. It is built after the reply is generated and only appended.
  `ParsedMessage` gained `to` and `cc` for the header block.

## Considered Alternatives

- **bleach**: deprecated by its maintainers since 2023.
- **lxml_html_clean**: blocklist-based cleaning, split out of lxml for its security history. An allowlist is the safer
  default for sender markup.
- **Asking the model for HTML**: more tokens and more failure modes. The sanitiser would still be needed, and the
  plain-text alternative would have to be derived from HTML.

## Consequences

- Two new runtime dependencies in `packages/agent`: `nh3` (Rust `ammonia` bindings, new to the lockfile) and
  `markdown-it-py` (already in the lockfile through `rich`).
- Drafts change shape for every profile, including those with quoting off. A body that was plain text renders as
  paragraphs, and stray Markdown characters (`*`, `_`, leading `1.`) in a model's reply are now interpreted.
- Inline images of the original (signature logos) are not in the quote. Re-attaching them was out of scope for #369.
- Stored profiles keep their own draft prompt. An admin who wants highlighting adds the `==…==` instruction to it.
