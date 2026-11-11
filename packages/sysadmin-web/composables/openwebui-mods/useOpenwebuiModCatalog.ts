import { listOpenwebuiModCatalog, uploadOpenwebuiMod, type OpenWebuiModCatalogEntry } from '~/sdk/client'

export function useOpenwebuiModCatalog() {
  const cache = useQueryCache()
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
  const upload = useMutation({
    mutation: async (file: File) => {
      const source = await uploadOpenwebuiMod({ composable: '$fetch', body: file })
      cache.invalidateQueries({ key: ['openwebui-mod-catalog'] })
      cache.invalidateQueries({ key: ['openwebui-mod-revisions', source.manifest.id] })
      return source
    },
  })
  return { catalog, upload }
}
