import { deleteUserFile } from '@core/sdk/client'

export const useDeleteUserFile = defineMutation(() => {
  const queryCache = useQueryCache()
  const { tenantId } = useTenant()

  const { mutateAsync: deleteUserFileMutation } = useMutation({
    mutation: async (filePath: string) => {
      await deleteUserFile({ composable: '$fetch', path: { tenant_id: tenantId.value! }, query: { path: filePath } })
    },
    onSettled: () => queryCache.invalidateQueries({ key: ['tenant', tenantId.value, 'user-files'] }),
  })

  return { deleteUserFile: deleteUserFileMutation }
})
