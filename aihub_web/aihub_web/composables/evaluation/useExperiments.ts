import {
  getExperiments,
  type MinimalExperiment,
} from '@core/sdk/client'
import { useQuery } from '@pinia/colada'
import { minutesToMilliseconds } from 'date-fns'

export const useExperiments = defineQuery(() => {
  const { data: experiments, isPending: experimentsAreLoading } = useQuery<MinimalExperiment[]>({
    key: () => ['experiments'],
    staleTime: minutesToMilliseconds(5),
    enabled: true,
    query: async () => {
      return await getExperiments({
        composable: '$fetch',
      })
    },
  })
  return {
    experiments,
    experimentsAreLoading,
  }
})
