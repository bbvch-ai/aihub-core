import { createDataset as createDatasetCall, type DatasetCreate } from '@core/sdk/client'

export const useCreateDataset = () => {
  const queryCache = useQueryCache()

  const { mutateAsync: createDataset } = useMutation({
    mutation: async ({ dataset, tenantId }: { dataset: DatasetCreate, tenantId: string }) => {
      await createDatasetCall({
        composable: '$fetch',
        path: { tenant_id: tenantId },
        body: dataset,
      })
      queryCache.invalidateQueries({ key: ['datasets'] })
    },
  })
  return {
    createDataset,
  }
}
