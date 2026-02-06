import { getLitellmModels, type ModelTypeGroupDto } from '@core/sdk/client'
import { useQuery } from '@pinia/colada'
import { minutesToMilliseconds } from 'date-fns'

export const useModelsList = defineQuery(() => {
  const { data: modelTypes, isPending: modelsAreLoading, error } = useQuery<ModelTypeGroupDto[]>({
    key: () => ['models'],
    staleTime: minutesToMilliseconds(5),
    enabled: true,
    query: async () => {
      return await getLitellmModels({
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
