import { getSupportedFileTypes } from '@core/sdk/client'
import { minutesToMilliseconds } from 'date-fns'

export const useSupportedFileTypes = defineQuery(() => {
  const { tenantId } = useTenant()

  const { data: supportedFileTypes } = useQuery<string[]>({
    key: () => ['supportedFileTypes', tenantId.value],
    staleTime: minutesToMilliseconds(60),
    enabled: computed(() => !!tenantId.value),
    query: async () => {
      return await getSupportedFileTypes({
        composable: '$fetch',
        path: { tenant_id: tenantId.value! },
      })
    },
  })

  return {
    supportedFileTypes,
  }
})
