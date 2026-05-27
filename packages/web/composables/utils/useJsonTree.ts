import type { TreeNode } from 'primevue/treenode'

interface JsonTreeOptions {
  maxDepth?: number
  expandLevel?: number
}

export const useJsonTree = () => {
  const convertJsonToTree = (
    data: unknown,
    key: string = 'root',
    options: JsonTreeOptions = {},
  ): TreeNode[] => {
    const { maxDepth = 10, expandLevel = 2 } = options

    const createNode = (
      value: unknown,
      label: string,
      depth: number = 0,
      parentPath: string = '',
    ): TreeNode => {
      const currentPath = parentPath ? `${parentPath}.${label}` : label
      const nodeKey = `${key}_${currentPath}_${depth}`.replaceAll(/[^a-zA-Z0-9_.-]/g, '_')

      if (value === null) {
        return {
          key: nodeKey,
          label: `${label}: null`,
          type: 'null',
          leaf: true,
        }
      }

      if (value === undefined) {
        return {
          key: nodeKey,
          label: `${label}: undefined`,
          type: 'undefined',
          leaf: true,
        }
      }

      const valueType = typeof value

      if (valueType === 'string') {
        return {
          key: nodeKey,
          label: `${label}: "${value}"`,
          type: 'string',
          leaf: true,
        }
      }

      if (valueType === 'number' || valueType === 'boolean') {
        return {
          key: nodeKey,
          label: `${label}: ${value}`,
          type: valueType,
          leaf: true,
        }
      }

      if (Array.isArray(value)) {
        const arrayLabel = `${label} [${value.length}]`

        if (depth >= maxDepth) {
          return {
            key: nodeKey,
            label: `${arrayLabel}: [max depth reached]`,
            type: 'array',
            leaf: true,
          }
        }

        const children = value.map((item, index) =>
          createNode(item, `[${index}]`, depth + 1, currentPath),
        )

        return {
          key: nodeKey,
          label: arrayLabel,
          type: 'array',
          leaf: children.length === 0,
          children,
          expanded: depth < expandLevel,
        }
      }

      if (valueType === 'object') {
        const entries = Object.entries(value)
        const objectLabel = `${label} {${entries.length}}`

        if (depth >= maxDepth) {
          return {
            key: nodeKey,
            label: `${objectLabel}: {max depth reached}`,
            type: 'object',
            leaf: true,
          }
        }

        const children = entries.map(([objKey, objValue]) =>
          createNode(objValue, objKey, depth + 1, currentPath),
        )

        return {
          key: nodeKey,
          label: objectLabel,
          type: 'object',
          leaf: children.length === 0,
          children,
          expanded: depth < expandLevel,
        }
      }

      // Fallback for unknown types
      return {
        key: nodeKey,
        label: `${label}: ${String(value)}`,
        type: 'unknown',
        leaf: true,
      }
    }

    if (typeof data === 'object' && data !== null) {
      const entries = Object.entries(data)
      return entries.map(([objKey, objValue]) =>
        createNode(objValue, objKey, 0, ''),
      )
    }

    return [createNode(data, 'value', 0, '')]
  }

  return {
    convertJsonToTree,
  }
}
