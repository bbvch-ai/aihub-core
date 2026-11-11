import type { Ref } from 'vue'
import {
  getOpenwebuiModHost,
  listOpenwebuiModPublications,
  listOpenwebuiModRevisions,
  publishOpenwebuiMod,
  type OpenWebuiModRevisionResponse,
} from '~/sdk/client'

export function useOpenwebuiModVersions(modId: Ref<string>, initial?: OpenWebuiModRevisionResponse) {
  const cache = useQueryCache()
  const offset = ref(0)
  const selected = ref(initial)
  const host = useQuery({
    key: ['openwebui-mod-host'],
    query: () => getOpenwebuiModHost({ composable: '$fetch' }),
  })
  const revisions = useQuery({
    key: () => ['openwebui-mod-revisions', modId.value, offset.value],
    query: () => listOpenwebuiModRevisions({ composable: '$fetch', query: { mod_id: modId.value, offset: offset.value, limit: 50 } }),
  })
  watch(revisions.data, value => { if (!selected.value && value?.length) selected.value = value[0] }, { immediate: true })
  const publications = useQuery({
    key: () => ['openwebui-mod-publications', selected.value?.revision ?? ''],
    enabled: () => Boolean(selected.value),
    query: () => listOpenwebuiModPublications({ composable: '$fetch', path: { revision: selected.value!.revision } }),
  })
  const publish = useMutation({
    mutation: async (revision: string) => {
      const publication = await publishOpenwebuiMod({ composable: '$fetch', path: { revision } })
      cache.invalidateQueries({ key: ['openwebui-mod-publications', revision] })
      return { publication, warnings: publication.manifest.warnings ?? [] }
    },
  })
  return { offset, selected, host, revisions, publications, publish }
}
