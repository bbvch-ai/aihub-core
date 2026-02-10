import { type Dataset, getDataset } from '@core/sdk/client'
import { useQuery } from '@pinia/colada'
import { minutesToMilliseconds } from 'date-fns'

export const useDataset = defineQuery(() => {
  const route = useRoute()
  const isRouteReady = useRouteReady('dataset_id')

  const { data: dataset, isPending: datasetIsLoading } = useQuery<Dataset>({
    key: () => ['datasets', route.params.dataset_id as string],
    staleTime: minutesToMilliseconds(5),
    enabled: isRouteReady,
    query: async () => {
      return await getDataset({
        composable: '$fetch',
        path: {
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
