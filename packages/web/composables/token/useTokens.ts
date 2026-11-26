import { listTokensEndpoint, type TokenResponse } from '@core/sdk/client'
import { minutesToMilliseconds } from 'date-fns'

// Keyed without the tenant: a token belongs to its user, so every tenant lists the same ones.
export const useTokens = defineQuery(() => {
  const { tenantId } = useTenant()

  const { data: tokens, isPending: tokensAreLoading } = useQuery<TokenResponse[]>({
    key: () => ['tokens'],
    staleTime: minutesToMilliseconds(5),
    enabled: useTenantReady(),
    query: async () => await listTokensEndpoint({ composable: '$fetch', path: { tenant_id: tenantId.value! } }),
  })

  return { tokens, tokensAreLoading }
})
