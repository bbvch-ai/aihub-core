import { type EvaluationDatasetCreateDto, createDatasetEndpoint } from '@core/sdk/client'

export const useCreateDataset = () => {
  const queryCache = useQueryCache()

  const { mutate: createDataset } = useMutation({
    mutation: async ({ dataset }: { dataset: EvaluationDatasetCreateDto }) => {
      await createDatasetEndpoint({
        composable: '$fetch',
        body: dataset,
      })
      queryCache.invalidateQueries({ key: ['datasets'] })
    },
  })
  return {
    createDataset,
  }
}
