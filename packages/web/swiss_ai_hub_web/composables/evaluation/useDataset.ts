import { type Dataset, getDataset } from '@core/sdk/client'
import { useQuery } from '@pinia/colada'
import { minutesToMilliseconds } from 'date-fns'

export const useDataset = defineQuery(() => {
  const route = useRoute()
  const { tenantName } = useTenantFromRoute()
  const isRouteReady = useRouteReady('dataset_id')

  const { data: dataset, isPending: datasetIsLoading } = useQuery<Dataset>({
    key: () => ['datasets', tenantName.value, route.params.dataset_id as string],
    staleTime: minutesToMilliseconds(5),
    enabled: computed(() => isRouteReady.value && !!tenantName.value),
    query: async () => {
      return await getDataset({
        composable: '$fetch',
        path: {
          tenant_id: tenantName.value!,
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
