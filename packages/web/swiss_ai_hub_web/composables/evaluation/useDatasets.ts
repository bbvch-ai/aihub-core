import {
  getDatasets,
  type MinimalDataset,
} from '@core/sdk/client'
import { useQuery } from '@pinia/colada'
import { minutesToMilliseconds } from 'date-fns'

export const useDatasets = defineQuery(() => {
  const { tenantId } = useTenant()

  const { data: datasets, isPending: datasetsAreLoading } = useQuery<MinimalDataset[]>({
    key: () => ['tenant', tenantId.value, 'datasets'],
    staleTime: minutesToMilliseconds(5),
    enabled: useTenantReady(),
    query: async () => {
      return await getDatasets({
        composable: '$fetch',
        path: { tenant_id: tenantId.value! },
      })
    },
  })
  return {
    datasets,
    datasetsAreLoading,
  }
})
