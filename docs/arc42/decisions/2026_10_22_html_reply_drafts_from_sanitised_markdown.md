# Reply Drafts Are HTML Rendered from Markdown and Sanitised with nh3

## Context

The mailbox agents (`ImapAgent`, `EmailClassificationAgent`) left every reply draft as a single `text/plain` part. Two
customer requests needed more than that:

- aihub-core-private#368: formatting in the draft, above all highlighting a sentence in yellow so the reviewer sees it.
  HTML the model wrote showed up as literal tags.
- aihub-core-private#369: the original email quoted below the reply, the way a reply in Outlook does, with a header
  block and the original's own HTML body.

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

- **Markdown in, HTML out.** `DraftBodyRenderer` renders the model's body with `markdown-it-py` (CommonMark plus tables
  and linkify). Raw HTML in the output is escaped, never parsed. Replies routinely contain angle brackets that are not
  markup, such as a `<Ihr Name>` sign-off placeholder or `a<b` in a comparison. Parsing those as tags made them vanish,
  or left the rest of the reply bold.
- **Highlighting is a parser rule.** `==text==` is the highlight syntax the default prompt offers.
  `HighlightMarkdownRule` registers it with markdown-it as a paired delimiter, like strikethrough, so code spans and
  autolinks are never touched. Like `_emphasis_`, it never opens or closes inside a word, so `status==active` stays
  text. No `mark` plugin exists in `mdit-py-plugins` (0.6.1), and the JavaScript `markdown-it-mark` plugin would match
  inside words. The rule emits `<mark>`, which the sanitiser turns into `<span style="background-color:#ffff00">`,
  because Outlook ignores `<mark>`.
- **Bare URLs are links.** Drafting prompts quote plain addresses (`https://…`, `www.…`), and CommonMark leaves them as
  text. `LinkifyMarkdownRule` turns on markdown-it's linkify (`linkify-it-py`) with fuzzy matching off, plus a `www.`
  schema. Fuzzy matching takes any word ending in a country code for a domain, so `bericht.py` would have become a link;
  a bare `sgum.ch` therefore stays text. A `www.` address is linked over `https://`.
- **nh3 is the sanitiser.** `MailHtmlSanitizer` holds two allowlists: a narrow one for the reply (text formatting, lists
  with their `start` number, tables, links, `background-color`/`color` styles) and a wider one for the quoted original
  that keeps its layout (tables, fonts, spacing CSS). Neither allows `img`. `script`, `style`, `title` and `head` lose
  their content. Links are restricted to `http`, `https` and `mailto`.
- **Every draft is `multipart/alternative`.** The plain-text part is derived from the sanitised HTML, not from the
  Markdown source. It keeps line breaks, list bullets and numbers (from the list's `start`), and each link's target next
  to its text (`the docs <https://…>`). Stripping tags from the source had dropped autolinked addresses such as
  `<alice@example.com>`.
- **Quoting is a toggle** (`DraftEmailSettings.quote_original`, off by default). `QuotedOriginal` builds the separator,
  a From/Sent/To/Cc/Subject block in the profile's `quote_locale` (labels and date format in `lib.imap.quote.*`) and the
  sanitised original, or its text body escaped when it has no HTML. It is built after the reply is generated and only
  appended. `ParsedMessage` gained `to` and `cc` for the header block; a sender-written encoded line break makes the
  address parser raise, so an unreadable To or Cc is left out rather than failing a batch that would fail on every run.
  The Sent date is converted to the profile's `quote_timezone` (default `Europe/Zurich`), as Outlook shows it in the
  replier's zone, and both the header block and the quoted body name Outlook's default font: the sanitiser drops the
  original's `<style>` sheet, and Word falls back to Times New Roman for text that no longer names one.

## Considered Alternatives

- **bleach**: deprecated by its maintainers since 2023.
- **lxml_html_clean**: blocklist-based cleaning, split out of lxml for its security history. An allowlist is the safer
  default for sender markup.
- **Asking the model for HTML**: more tokens and more failure modes. The sanitiser would still be needed, and the
  plain-text alternative would have to be derived from HTML.

## Consequences

- Three new runtime dependencies in `packages/agent`: `nh3` (Rust `ammonia` bindings, new to the lockfile),
  `markdown-it-py` (already in the lockfile through `rich`) and `linkify-it-py` (new, pure Python, with `uc-micro-py`).
- The quote's language is a profile setting, not the run's locale. Outlook labels a quote in the replier's language, and
  a scheduled run carries the platform default (`de`) whoever owns the mailbox.
- Drafts change shape for every profile, including those with quoting off. A body that was plain text renders as
  paragraphs, and stray Markdown characters (`*`, `_`, leading `1.`) in a model's reply are now interpreted. A paragraph
  opening with a number and a dot (`31. Oktober …`) becomes a list starting at that number: it reads the same, but is
  indented.
- A model that answers a highlighting request with HTML (`<span style="background:yellow">`) gets that HTML shown as
  text. The prompt has to ask for `==…==`.
- Inline images of the original (signature logos) are not in the quote. Re-attaching them was out of scope for #369.
- Stored profiles keep their own draft prompt. An admin who wants highlighting adds the `==…==` instruction to it.
