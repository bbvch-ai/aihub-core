import { getModel, type ModelDtoReadable } from '@core/sdk/client'
import { useQuery } from '@pinia/colada'
import { minutesToMilliseconds } from 'date-fns'

export const useSingleModel = () => {
  const route = useRoute()

  const modelName = computed<string>(() => decodeURIComponent(route.params?.model_name as string))

  const { data: model, isPending: modelIsLoading, error } = useQuery<ModelDtoReadable>({
    key: () => ['model', modelName.value],
    staleTime: minutesToMilliseconds(5),
    enabled: () => !!modelName.value,
    query: async () => {
      return await getModel({
        composable: '$fetch',
        path: {
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
