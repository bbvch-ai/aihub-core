import { getLitellmModelsByMode, type ModelDto } from '@core/sdk/client'
import { minutesToMilliseconds } from 'date-fns'

type ModelMode = 'chat' | 'embedding' | 'rerank' | 'image_generation' | 'audio_transcription' | 'audio_speech'

/**
 * Models the gateway serves for one mode, filtered to what this tenant may use.
 *
 * Separate from `useModelsList`, which returns every mode grouped: a picker for a single slot only ever
 * wants one mode, and offering a chat model where an embedding model belongs is rejected by the API.
 */
export const useModelsByMode = (mode: MaybeRefOrGetter<ModelMode>) => {
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
