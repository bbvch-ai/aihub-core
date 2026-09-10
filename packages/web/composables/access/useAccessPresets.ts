import { type AccessPresetDto, getAccessPresets } from '@core/sdk/client'
import { minutesToMilliseconds } from 'date-fns'

export default defineQuery(() => {
  const { tenantId } = useTenant()
  // Presets are tenant-independent; fall back to 'active' so the editor works on the
  // configure-new-tenant route (which has no tenant param). See useAccessCapabilities.
  const targetTenantId = computed(() => tenantId.value ?? 'active')

  const {
    data: presets,
    isPending: presetsAreLoading,
  } = useQuery<AccessPresetDto[]>({
    key: () => ['tenant', targetTenantId.value, 'access-presets'],
    staleTime: minutesToMilliseconds(30),
    query: async () => {
      return await getAccessPresets({
        composable: '$fetch',
        path: { tenant_id: targetTenantId.value },
      })
    },
  })

  return {
    presets,
    presetsAreLoading,
  }
})
