import { getLitellmModels, type ModelTypeGroupDto } from '@core/sdk/client'
import { useQuery } from '@pinia/colada'
import { minutesToMilliseconds } from 'date-fns'

export const useModelsList = defineQuery(() => {
  const { tenantName } = useTenantFromRoute()

  const { data: modelTypes, isPending: modelsAreLoading, error } = useQuery<ModelTypeGroupDto[]>({
    key: () => ['models', tenantName.value],
    staleTime: minutesToMilliseconds(5),
    enabled: computed(() => !!tenantName.value),
    query: async () => {
      return await getLitellmModels({
        composable: '$fetch',
        path: { tenant_id: tenantName.value! },
      })
    },
  })

  return {
    modelTypes,
    modelsAreLoading,
    error,
  }
})
