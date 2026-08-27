import { getLitellmModelsByMode, type ModelDto } from '@core/sdk/client'
import { minutesToMilliseconds } from 'date-fns'

import type { MaybeRefOrGetter } from 'vue'

/**
 * Models available for one LiteLLM mode. A plain composable rather than `defineQuery` because the
 * key depends on a per-instance argument (see `useSingleModel`). The shared query cache is what
 * matters here: a form renders several model fields and re-renders remount them, and an uncached
 * per-mount fetch turned that into a request storm.
 */
export const useModelsByMode = (mode: MaybeRefOrGetter<string>) => {
  const { tenantId } = useTenant()

  const { data: models, isPending: modelsAreLoading } = useQuery<ModelDto[]>({
    key: () => ['tenant', tenantId.value, 'models', 'mode', toValue(mode)],
    staleTime: minutesToMilliseconds(5),
    enabled: useTenantReady(),
    query: async () => {
      return await getLitellmModelsByMode({
        composable: '$fetch',
        path: { tenant_id: tenantId.value!, mode: toValue(mode) },
      })
    },
  })

  return {
    models,
    modelsAreLoading,
  }
}
