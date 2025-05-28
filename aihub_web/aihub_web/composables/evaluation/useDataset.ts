import { type Dataset, getDataset } from '@core/sdk/client'
import { useQuery } from '@pinia/colada'

export const useDataset = defineQuery(() => {
  const route = useRoute()
  const { data: dataset, isPending: datasetIsLoading } = useQuery<Dataset>({
    key: () => ['datasets', route.params.dataset_id as string],
    staleTime: 1000 * 60 * 5, // 5 minutes
    enabled: true,
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
