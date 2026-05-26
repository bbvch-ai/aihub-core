import { getLitellmModels, type ModelTypeGroupDto } from '@core/sdk/client'
import { minutesToMilliseconds } from 'date-fns'

export const useModelsList = defineQuery(() => {
  const { tenantId } = useTenant()

  const { data: modelTypes, isPending: modelsAreLoading, error } = useQuery<ModelTypeGroupDto[]>({
    key: () => ['tenant', tenantId.value, 'models'],
    staleTime: minutesToMilliseconds(5),
    enabled: useTenantReady(),
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
