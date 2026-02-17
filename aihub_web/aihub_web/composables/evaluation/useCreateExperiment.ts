import { runExperiment, type ExperimentCreate } from '@core/sdk/client'

export const useCreateExperiment = () => {
  const queryCache = useQueryCache()

  const { mutateAsync: createExperiment } = useMutation({
    mutation: async ({ experiment }: { experiment: ExperimentCreate }) => {
      await runExperiment({
        composable: '$fetch',
        body: experiment,
      })
      new Promise(r => setTimeout(r, 500)).then(() => {
        queryCache.invalidateQueries({ key: ['experiments'] })
      })
    },
  })
  return {
    createExperiment,
  }
}
