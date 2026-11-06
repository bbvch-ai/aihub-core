import type { Options as SanitizeSchema } from 'rehype-sanitize'

// Markdown rendered here comes from users, ingested documents and LLM output, so only prose survives. The schema is
// serialised into the MDC parser's generated config, so it must stay plain JSON (no RegExp, no functions).
export const markdownSanitizeSchema: SanitizeSchema = {
  tagNames: [
    'a', 'b', 'blockquote', 'br', 'caption', 'code', 'dd', 'del', 'details', 'div', 'dl', 'dt', 'em',
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'hr', 'i', 'img', 'input', 'ins', 'kbd', 'li', 'mark', 'ol', 'p', 'pre',
    'q', 's', 'samp', 'section', 'small', 'span', 'strike', 'strong', 'sub', 'summary', 'sup',
    'table', 'tbody', 'td', 'tfoot', 'th', 'thead', 'tr', 'u', 'ul', 'var',
    'markdown-figure', 'markdown-table',
  ],
  attributes: {
    'a': [
      'href', 'title', 'dataFootnoteRef', 'dataFootnoteBackref', 'ariaDescribedBy', 'ariaLabel',
      ['className', 'data-footnote-backref'],
      ['rel', 'nofollow', 'noopener', 'noreferrer'],
      ['target', '_blank'],
    ],
    'blockquote': ['cite'],
    'del': ['cite'],
    'details': ['open'],
    'h2': ['id', ['className', 'sr-only']],
    'img': ['src', 'alt', 'title', 'width', 'height'],
    'input': ['checked', ['disabled', true], ['type', 'checkbox']],
    'ins': ['cite'],
    'li': ['id', ['className', 'task-list-item']],
    'ol': ['start', ['className', 'contains-task-list']],
    'q': ['cite'],
    'section': ['dataFootnotes', ['className', 'footnotes']],
    'td': ['align', 'colSpan', 'rowSpan'],
    'th': ['align', 'colSpan', 'rowSpan', 'scope'],
    'ul': [['className', 'contains-task-list']],
    '*': ['id'],
  },
  ancestors: {
    tbody: ['table'],
    td: ['table'],
    tfoot: ['table'],
    th: ['table'],
    thead: ['table'],
    tr: ['table'],
  },
  protocols: {
    cite: ['http', 'https'],
    href: ['http', 'https', 'mailto'],
    // ResolveImageComponent turns s3:// figure paths of ingested documents into presigned URLs.
    src: ['http', 'https', 's3'],
  },
  required: {
    input: { disabled: true, type: 'checkbox' },
  },
  clobber: ['ariaDescribedBy', 'ariaLabelledBy', 'id', 'name'],
  clobberPrefix: 'user-content-',
  strip: ['script', 'style', 'template', 'title', 'noscript', 'textarea', 'select'],
  allowComments: false,
  allowDoctypes: false,
}
