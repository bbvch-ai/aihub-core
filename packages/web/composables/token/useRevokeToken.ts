import { revokeTokenEndpoint } from '@core/sdk/client'

export const useRevokeToken = defineMutation(() => {
  const queryCache = useQueryCache()

  const { mutateAsync: revokeToken } = useMutation({
    mutation: async ({ tokenId, tenantId }: { tokenId: string, tenantId: string }) => {
      await revokeTokenEndpoint({ composable: '$fetch', path: { tenant_id: tenantId, token_id: tokenId } })
    },
    onSettled: () => queryCache.invalidateQueries({ key: ['tokens'] }),
  })

  return { revokeToken }
})
