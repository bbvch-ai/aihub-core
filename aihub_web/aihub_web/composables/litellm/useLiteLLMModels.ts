import { useQuery } from '@pinia/colada'
import { minutesToMilliseconds } from 'date-fns'

export const useLiteLLMModels = defineQuery(() => {
  const { data: models, isPending: modelsAreLoading, error } = useQuery({
    key: () => ['litellm', 'models'],
    staleTime: minutesToMilliseconds(5),
    enabled: true,
    query: async () => {
      return await $fetch('/api/v1/litellm/model_info')
    },
  })
  
  return {
    models,
    modelsAreLoading,
    error,
  }
})