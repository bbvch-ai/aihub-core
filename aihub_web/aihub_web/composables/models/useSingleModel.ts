import { getModel, type ModelDto } from '@core/sdk/client'
import { useQuery } from '@pinia/colada'
import { minutesToMilliseconds } from 'date-fns'

export const useSingleModel = (modelName: MaybeRefOrGetter<string>) => {
  const { data: model, isPending: modelIsLoading, error } = useQuery<ModelDto>({
    key: () => ['model', toValue(modelName)],
    staleTime: minutesToMilliseconds(5),
    enabled: () => !!toValue(modelName),
    query: async () => {
      return await getModel({
        composable: '$fetch',
        path: {
          model_name: toValue(modelName),
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
