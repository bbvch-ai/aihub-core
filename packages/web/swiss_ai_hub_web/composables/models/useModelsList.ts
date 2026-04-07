import { getLitellmModels, type ModelTypeGroupDto } from '@core/sdk/client'
import { useQuery } from '@pinia/colada'
import { minutesToMilliseconds } from 'date-fns'

export const useModelsList = defineQuery(() => {
  const { tenantId } = useTenant()

  const { data: modelTypes, isPending: modelsAreLoading, error } = useQuery<ModelTypeGroupDto[]>({
    key: () => ['models', tenantId.value],
    staleTime: minutesToMilliseconds(5),
    enabled: computed(() => !!tenantId.value),
    query: async () => {
      return await getLitellmModels({
        composable: '$fetch',
        path: { tenant_id: tenantId.value! },
      })
    },
  })

  return {
    modelTypes,
    modelsAreLoading,
    error,
  }
})
