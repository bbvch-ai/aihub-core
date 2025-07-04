import { type DatasetUpdate, updateDataset as updateDatasetCall } from '@core/sdk/client'

export const useUpdateDataset = () => {
  const queryCache = useQueryCache()
  const route = useRoute()

  const { mutateAsync: updateDataset } = useMutation({
    mutation: async ({ dataset }: { dataset: DatasetUpdate }) => {
      await updateDatasetCall({
        composable: '$fetch',
        body: dataset,
        path: {
          dataset_id: route.params.dataset_id as string,
        },
      })
      queryCache.invalidateQueries({ key: ['datasets'] })
    },
  })
  return {
    updateDataset,
  }
}
