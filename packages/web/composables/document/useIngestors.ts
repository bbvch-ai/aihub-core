import { getIngestors, type IngestorDto } from '@core/sdk/client'
import { minutesToMilliseconds } from 'date-fns'

export const useIngestors = defineQuery(() => {
  const { tenantId } = useTenant()

  const { data: ingestors, isPending: ingestorsAreLoading } = useQuery<IngestorDto[]>({
    key: () => ['tenant', tenantId.value, 'ingestors'],
    staleTime: minutesToMilliseconds(5),
    enabled: useTenantReady(),
    query: async () => {
      return await getIngestors({
        composable: '$fetch',
        path: { tenant_id: tenantId.value! },
      })
    },
  })

  return {
    ingestors,
    ingestorsAreLoading,
  }
})
