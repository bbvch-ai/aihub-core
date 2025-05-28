import {
  getExperiments,
  type MinimalExperiment,
} from '@core/sdk/client'
import { useQuery } from '@pinia/colada'

export const useExperiments = defineQuery(() => {
  const { data: experiments, isPending: experimentsAreLoading } = useQuery<MinimalExperiment[]>({
    key: () => ['experiments'],
    staleTime: 1000 * 60 * 5, // 5 minutes
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
