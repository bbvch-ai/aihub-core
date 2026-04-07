import { getLitellmModel, type ModelDto } from '@core/sdk/client'
import { useQuery } from '@pinia/colada'
import { minutesToMilliseconds } from 'date-fns'

export const useSingleModel = () => {
  const route = useRoute()
  const { tenantName } = useTenantFromRoute()

  const modelName = computed<string>(() => decodeURIComponent(route.params?.model_name as string))

  const { data: model, isPending: modelIsLoading, error } = useQuery<ModelDto>({
    key: () => ['model', tenantName.value, modelName.value],
    staleTime: minutesToMilliseconds(5),
    enabled: () => !!modelName.value && !!tenantName.value,
    query: async () => {
      return await getLitellmModel({
        composable: '$fetch',
        path: {
          tenant_id: tenantName.value!,
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
