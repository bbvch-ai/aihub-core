import { type ModelDTO, modelList } from '@core/sdk/client'
import { useQuery } from '@pinia/colada'
import { minutesToMilliseconds } from 'date-fns'

export const useModelsList = defineQuery(() => {
  const { data: rawModels, isPending: modelsAreLoading, error } = useQuery<ModelDTO[]>({
    key: () => ['models', 'models'],
    staleTime: minutesToMilliseconds(5),
    enabled: true,
    query: async () => {
      return await modelList({
        composable: '$fetch',
      })
    },
  })

  const modelTypes = computed(() => {
    if (!rawModels.value) return []

    const grouped = new Map()

    rawModels.value.forEach((model: ModelDTO) => {
      const modelType = model.model_info.mode || t('models.otherModels')
      if (!grouped.has(modelType)) {
        grouped.set(modelType, {
          name: modelType,
          models: [],
        })
      }
      grouped.get(modelType).models.push(model)
    })

    return Array.from(grouped.values()).sort((a, b) => a.name.localeCompare(b.name))
  })

  return {
    modelTypes,
    modelsAreLoading,
    error,
  }
})
