import {useQuery} from '@pinia/colada'
import {minutesToMilliseconds} from 'date-fns'

export const useModelsList = defineQuery(() => {
  const {data: models, isPending: modelsAreLoading, error} = useQuery({
    key: () => ['models', 'models'],
    staleTime: minutesToMilliseconds(5),
    enabled: true,
    query: async () => {
      return await $fetch('/api/v1/models/model_list')
    },
  })

  return {
    models,
    modelsAreLoading,
    error,
  }
})
