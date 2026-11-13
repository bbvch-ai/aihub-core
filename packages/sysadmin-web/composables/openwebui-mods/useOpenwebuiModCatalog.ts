import { listOpenwebuiModCatalog, type OpenWebuiModCatalogEntry } from '~/sdk/client'

export function useOpenwebuiModCatalog() {
  const catalog = useQuery({
    key: ['openwebui-mod-catalog'],
    query: async () => {
      const entries: OpenWebuiModCatalogEntry[] = []
      for (let offset = 0; ; offset += 100) {
        const page = await listOpenwebuiModCatalog({ composable: '$fetch', query: { offset, limit: 100 } })
        entries.push(...page)
        if (page.length < 100) return entries
      }
    },
  })
  return { catalog }
}
