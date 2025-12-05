import { getModels, type ModelTypeGroupDtoReadable } from '@core/sdk/client'
import { useQuery } from '@pinia/colada'
import { minutesToMilliseconds } from 'date-fns'

export const useModelsList = defineQuery(() => {
  const { data: modelTypes, isPending: modelsAreLoading, error } = useQuery<Array<ModelTypeGroupDtoReadable>>({
    key: () => ['models'],
    staleTime: minutesToMilliseconds(5),
    enabled: true,
    query: async () => {
      return await getModels({
        composable: '$fetch',
      })
    },
  })

  return {
    modelTypes,
    modelsAreLoading,
    error,
  }
})
