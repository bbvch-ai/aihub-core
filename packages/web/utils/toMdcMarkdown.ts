// Extracted documents wrap their figures and tables in <figure>/<table> tags for the backend's node parser. MDC does
// not parse markdown inside an HTML block, so the tags become the MDC components that render their content instead.
export const toMdcMarkdown = (markdown: string): string => markdown
  .replace(/(?:<|&lt;)figure(?:>|&gt;)/g, '::MarkdownFigure\n')
  .replace(/(?:<|&lt;)\/figure(?:>|&gt;)/g, '\n::')
  .replace(/(?:<|&lt;)table(?:>|&gt;)/g, '::MarkdownTable\n')
  .replace(/(?:<|&lt;)\/table(?:>|&gt;)/g, '\n::')
