import { moveUserFile } from '@core/sdk/client'

export const useMoveUserFile = defineMutation(() => {
  const queryCache = useQueryCache()
  const { tenantId } = useTenant()

  const { mutateAsync: moveUserFileMutation } = useMutation({
    mutation: async ({ source, destination }: { source: string, destination: string }) => {
      await moveUserFile({ composable: '$fetch', path: { tenant_id: tenantId.value! }, body: { source, destination } })
    },
    onSettled: () => queryCache.invalidateQueries({ key: ['tenant', tenantId.value, 'user-files'] }),
  })

  return { moveUserFile: moveUserFileMutation }
})
