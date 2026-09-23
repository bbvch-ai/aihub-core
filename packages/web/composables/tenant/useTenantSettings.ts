import { getTenantSettings } from '@core/sdk/client'

export const useTenantSettings = defineQuery(() => {
  const { tenantId } = useTenant()
  const { data: settings, isPending, error } = useQuery({
    key: () => ['tenant', tenantId.value ?? '', 'settings'],
    enabled: useTenantReady(),
    staleTime: 0,
    query: () => getTenantSettings({
      composable: '$fetch',
      path: { tenant_id: tenantId.value! },
    }),
  })
  return { settings, isPending, error }
})
