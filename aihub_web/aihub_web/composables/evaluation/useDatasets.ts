import {
  getDatasets,
  type MinimalDataset,
} from '@core/sdk/client'
import { useQuery } from '@pinia/colada'
import { minutesToMilliseconds } from 'date-fns'

export const useDatasets = defineQuery(() => {
  const { data: datasets, isPending: datasetsAreLoading } = useQuery<MinimalDataset[]>({
    key: () => ['datasets'],
    staleTime: minutesToMilliseconds(5),
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
