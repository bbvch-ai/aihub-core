import { createTokenEndpoint, type CreateTokenRequest, type CreateTokenResponse } from '@core/sdk/client'

// Deliberately not a Pinia Colada mutation: a mutation entry keeps its result in the global mutation cache, and this
// result is the token itself, which must live no longer than the dialog that shows it once.
export const useCreateToken = () => {
  const queryCache = useQueryCache()

  const createToken = async ({ request, tenantId }: { request: CreateTokenRequest, tenantId: string }): Promise<CreateTokenResponse> => {
    const created = await createTokenEndpoint({ composable: '$fetch', path: { tenant_id: tenantId }, body: request })
    await queryCache.invalidateQueries({ key: ['tokens'] })
    return created
  }

  return { createToken }
}
