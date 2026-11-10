import type { Element, ElementContent, Root } from 'hast'

// MDC's compiler checks every href and src with decodeURIComponent and does not catch its URIError, so one malformed
// escape such as `#bad%` throws and blanks the whole message. Runs after rehype-sanitize and drops such URLs.
const URL_PROPERTIES = ['href', 'src'] as const

const elementsOf = (node: Root | ElementContent): Element[] => {
  const children = 'children' in node ? node.children : []
  const own = node.type === 'element' ? [node] : []
  return [...own, ...children.flatMap(child => elementsOf(child as ElementContent))]
}

const isDecodable = (url: string): boolean => {
  try {
    decodeURIComponent(url)
    return true
  }
  catch {
    return false
  }
}

export default function rehypeDropUndecodableUrls() {
  return (tree: Root): void => {
    for (const element of elementsOf(tree)) {
      for (const property of URL_PROPERTIES) {
        const url = element.properties?.[property]
        if (typeof url === 'string' && !isDecodable(url)) delete element.properties[property]
      }
    }
  }
}
