import { createDataset as createDatasetCall, type DatasetCreate } from '@core/sdk/client'

export const useCreateDataset = () => {
  const queryCache = useQueryCache()

  const { mutateAsync: createDataset } = useMutation({
    mutation: async ({ dataset }: { dataset: DatasetCreate }) => {
      await createDatasetCall({
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
