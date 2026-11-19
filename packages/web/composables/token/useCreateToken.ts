import { createTokenEndpoint, type CreateTokenRequest, type CreateTokenResponse } from '@core/sdk/client'

// Deliberately not a Pinia Colada mutation: a mutation entry keeps its result in the global mutation cache, and this
// result is the token itself, which must live no longer than the dialog that shows it once.
export const useCreateToken = () => {
  const queryCache = useQueryCache()

  const createToken = async ({ name, expiresAt, tenantId }: { name: string, expiresAt: Date, tenantId: string }): Promise<CreateTokenResponse> => {
    // The generated type says Date, but the Nuxt client's unwrapRefs copies a body's enumerable keys, and a Date has
    // none: it would arrive as {} and fail validation. An ISO string is what the API parses anyway.
    const body = { name, expiry_date: expiresAt.toISOString() } as unknown as CreateTokenRequest
    const created = await createTokenEndpoint({ composable: '$fetch', path: { tenant_id: tenantId }, body })
    await queryCache.invalidateQueries({ key: ['tokens'] })
    return created
  }

  return { createToken }
}
