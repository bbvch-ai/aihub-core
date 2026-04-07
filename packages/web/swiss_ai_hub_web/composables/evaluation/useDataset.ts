import { type Dataset, getDataset } from '@core/sdk/client'
import { useQuery } from '@pinia/colada'
import { minutesToMilliseconds } from 'date-fns'

export const useDataset = defineQuery(() => {
  const route = useRoute()
  const { tenantId } = useTenant()

  const { data: dataset, isPending: datasetIsLoading } = useQuery<Dataset>({
    key: () => ['tenant', tenantId.value, 'datasets', route.params.dataset_id as string],
    staleTime: minutesToMilliseconds(5),
    enabled: useTenantReady('dataset_id'),
    query: async () => {
      return await getDataset({
        composable: '$fetch',
        path: {
          tenant_id: tenantId.value!,
          dataset_id: route.params.dataset_id as string,
        },
      })
    },
  })
  return {
    dataset,
    datasetIsLoading,
  }
})
