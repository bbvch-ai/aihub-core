import { type Experiment, getExperiment } from '@core/sdk/client'
import { useQuery } from '@pinia/colada'

export const useExperiment = defineQuery(() => {
  const route = useRoute()
  const { data: experiment, isPending: experimentIsLoading } = useQuery<Experiment>({
    key: () => ['experiments', route.params.experiment_id as string],
    staleTime: 1000 * 60 * 5, // 5 minutes
    enabled: true,
    query: async () => {
      return await getExperiment({
        composable: '$fetch',
        path: {
          experiment_id: route.params.experiment_id as string,
        },
      })
    },
  })
  return {
    experiment,
    experimentIsLoading,
  }
})
