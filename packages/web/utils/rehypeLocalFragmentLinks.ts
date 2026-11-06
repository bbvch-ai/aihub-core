import type { Element, ElementContent, Root } from 'hast'

// rehype-sanitize prefixes every id with `user-content-` so markdown cannot clobber the page's own ids, but it leaves
// `href="#…"` alone, which breaks footnotes and in-document links. Runs after it: a local link whose prefixed target
// exists is pointed at that target; any other link stays as it was.
const PREFIX = 'user-content-'

const elementsOf = (node: Root | ElementContent): Element[] => {
  const children = 'children' in node ? node.children : []
  const own = node.type === 'element' ? [node] : []
  return [...own, ...children.flatMap(child => elementsOf(child as ElementContent))]
}

export default function rehypeLocalFragmentLinks() {
  return (tree: Root): void => {
    const elements = elementsOf(tree)
    const ids = new Set(elements.map(element => element.properties?.id).filter(id => typeof id === 'string'))
    for (const element of elements) {
      const href = element.properties?.href
      if (element.tagName !== 'a' || typeof href !== 'string' || !href.startsWith('#')) continue
      const target = `${PREFIX}${href.slice(1)}`
      if (ids.has(target)) element.properties.href = `#${target}`
    }
  }
}
