import { type Experiment, getExperiment } from '@core/sdk/client'
import { useQuery } from '@pinia/colada'
import { minutesToMilliseconds } from 'date-fns'

export const useExperiment = defineQuery(() => {
  const route = useRoute()
  const isRouteReady = useRouteReady('experiment_id')

  const { data: experiment, isPending: experimentIsLoading } = useQuery<Experiment>({
    key: () => ['experiments', route.params.experiment_id as string],
    staleTime: minutesToMilliseconds(5),
    enabled: isRouteReady,
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
