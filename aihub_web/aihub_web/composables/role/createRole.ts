import { createRole, type CreateRoleRequest } from '@core/sdk/client'

export const useCreateRole = defineMutation(() => {
  const queryCache = useQueryCache()

  const { mutateAsync: createRoleMutation } = useMutation({
    mutation: async ({ createdRole }: { createdRole: CreateRoleRequest }) => {
      await createRole({
        composable: '$fetch',
        body: createdRole,
      })
      queryCache.invalidateQueries({ key: ['roles'] })
    },
  })
  return {
    createRole: createRoleMutation,
  }
})
