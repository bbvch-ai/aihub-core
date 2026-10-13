import { createUserFolder } from '@core/sdk/client'

export const useCreateUserFolder = defineMutation(() => {
  const queryCache = useQueryCache()
  const { tenantId } = useTenant()

  const { mutateAsync: createUserFolderMutation } = useMutation({
    mutation: async (folderPath: string) => {
      await createUserFolder({ composable: '$fetch', path: { tenant_id: tenantId.value! }, body: { path: folderPath } })
    },
    onSettled: () => queryCache.invalidateQueries({ key: ['tenant', tenantId.value, 'user-files'] }),
  })

  return { createUserFolder: createUserFolderMutation }
})
