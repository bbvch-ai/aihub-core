import { type Dataset, getDataset } from '@core/sdk/client'
import { minutesToMilliseconds } from 'date-fns'

export const useDataset = defineQuery(() => {
  const route = useRoute()
  const { tenantId } = useTenant()

  const { data: dataset, isPending: datasetIsLoading } = useQuery<Dataset>({
    key: () => ['tenant', tenantId.value, 'datasets', route.params.dataset_id as string],
    staleTime: minutesToMilliseconds(5),
    enabled: useTenantReady('dataset_id'),
    query: async () => {
      const datasetId = route.params.dataset_id as string | undefined
      if (!datasetId) return

      return await getDataset({
        composable: '$fetch',
        path: {
          tenant_id: tenantId.value!,
          dataset_id: datasetId,
        },
      })
    },
  })
  return {
    dataset,
    datasetIsLoading,
  }
})
