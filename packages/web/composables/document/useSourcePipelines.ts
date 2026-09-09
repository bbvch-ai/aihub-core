import { getSourcePipelines, type SourcePipelineDto } from '@core/sdk/client'
import { minutesToMilliseconds } from 'date-fns'

export const useSourcePipelines = defineQuery(() => {
  const { tenantId } = useTenant()

  const { data: sourcePipelines, isPending: sourcePipelinesAreLoading } = useQuery<SourcePipelineDto[]>({
    key: () => ['tenant', tenantId.value, 'source-pipelines'],
    staleTime: minutesToMilliseconds(5),
    enabled: useTenantReady(),
    query: async () => {
      return await getSourcePipelines({
        composable: '$fetch',
        path: { tenant_id: tenantId.value! },
      })
    },
  })

  return {
    sourcePipelines,
    sourcePipelinesAreLoading,
  }
})
