import { getLitellmModel, type ModelDto } from '@core/sdk/client'
import { useQuery } from '@pinia/colada'
import { minutesToMilliseconds } from 'date-fns'

export const useSingleModel = () => {
  const route = useRoute()
  const { tenantId } = useTenant()

  const modelName = computed<string>(() => decodeURIComponent(route.params?.model_name as string))

  const { data: model, isPending: modelIsLoading, error } = useQuery<ModelDto>({
    key: () => ['tenant', tenantId.value, 'model', modelName.value],
    staleTime: minutesToMilliseconds(5),
    enabled: useTenantReady('model_name'),
    query: async () => {
      return await getLitellmModel({
        composable: '$fetch',
        path: {
          tenant_id: tenantId.value!,
          model_name: modelName.value,
        },
      })
    },
  })

  return {
    model,
    modelIsLoading,
    error,
  }
}
