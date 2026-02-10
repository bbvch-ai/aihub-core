import { type Dataset, getDataset } from '@core/sdk/client'
import { useQuery } from '@pinia/colada'
import { minutesToMilliseconds } from 'date-fns'

export const useDataset = defineQuery(() => {
  const route = useRoute()
  const datasetId = computed(() => route.params.dataset_id as string)
  const isRouteReady = computed(() => !!datasetId.value && !datasetId.value.startsWith('{'))

  const { data: dataset, isPending: datasetIsLoading } = useQuery<Dataset>({
    key: () => ['datasets', datasetId.value],
    staleTime: minutesToMilliseconds(5),
    enabled: isRouteReady,
    query: async () => {
      if (!isRouteReady.value) throw new Error('Route not ready')
      return await getDataset({
        composable: '$fetch',
        path: {
          dataset_id: datasetId.value,
        },
      })
    },
  })
  return {
    dataset,
    datasetIsLoading,
  }
})
