import { getSupportedFileTypes } from '@core/sdk/client'
import { minutesToMilliseconds } from 'date-fns'

export const useSupportedFileTypes = defineQuery(() => {
  const { tenantName } = useTenantFromRoute()

  const { data: supportedFileTypes } = useQuery<string[]>({
    key: () => ['supportedFileTypes', tenantName.value],
    staleTime: minutesToMilliseconds(60),
    enabled: computed(() => !!tenantName.value),
    query: async () => {
      return await getSupportedFileTypes({
        composable: '$fetch',
        path: { tenant_id: tenantName.value! },
      })
    },
  })

  return {
    supportedFileTypes,
  }
})
