import type { Ref } from 'vue'
import {
  getOpenwebuiModConfiguration,
  replaceOpenwebuiModConfiguration,
  getOpenwebuiGlobalMods,
  replaceOpenwebuiGlobalMods,
  type OpenWebuiModConfiguration,
  type OpenWebuiModGlobalState,
} from '~/sdk/client'

export function useOpenwebuiModSettings(tenantId: Ref<string>, globalScope = false) {
  const cache = useQueryCache()
  const configuration = useQuery({
    key: () => [globalScope ? 'openwebui-global-mod-settings' : 'openwebui-mod-settings', tenantId.value],
    query: async () => {
      const id = tenantId.value
      if (globalScope) {
        const globalState = await getOpenwebuiGlobalMods({ composable: '$fetch' })
        return { tenantId: id, configuration: globalState.configuration, globalState }
      }
      return { tenantId: id, configuration: await getOpenwebuiModConfiguration({ composable: '$fetch', path: { tenant_id: id } }), globalState: undefined as OpenWebuiModGlobalState | undefined }
    },
  })
  const save = useMutation({
    mutation: async ({ tenantId: id, configuration: value }: { tenantId: string, configuration: OpenWebuiModConfiguration }) => {
      const saved = globalScope
        ? (await replaceOpenwebuiGlobalMods({ composable: '$fetch', body: shallowRef(value) })).configuration
        : await replaceOpenwebuiModConfiguration({ composable: '$fetch', path: { tenant_id: id }, body: shallowRef(value) })
      cache.invalidateQueries({ key: [globalScope ? 'openwebui-global-mod-settings' : 'openwebui-mod-settings', id] })
      return saved
    },
  })
  return { configuration, save }
}
