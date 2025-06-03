import {
  getDatasets,
  type MinimalDataset,
} from '@core/sdk/client'
import { useQuery } from '@pinia/colada'

export const useDatasets = defineQuery(() => {
  const { data: datasets, isPending: datasetsAreLoading } = useQuery<MinimalDataset[]>({
    key: () => ['datasets'],
    staleTime: 1000 * 60 * 5, // 5 minutes
    enabled: true,
    query: async () => {
      return await getDatasets({
        composable: '$fetch',
      })
    },
  })
  return {
    datasets,
    datasetsAreLoading,
  }
})
