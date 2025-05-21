import { type EvaluationDatasetCreateDto, updateDatasetEndpoint } from '@core/sdk/client'

export const useUpdateDataset = () => {
  const queryCache = useQueryCache()

  const { mutate: createDataset } = useMutation({
    mutation: async ({ dataset }: { dataset: EvaluationDatasetCreateDto }) => {
      await updateDatasetEndpoint({
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
