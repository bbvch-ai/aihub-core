import {
  getDatasets,
  type MinimalDataset,
} from '@core/sdk/client'
import { useQuery } from '@pinia/colada'
import { minutesToMilliseconds } from 'date-fns'

export const useDatasets = defineQuery(() => {
  const { tenantName } = useTenantFromRoute()

  const { data: datasets, isPending: datasetsAreLoading } = useQuery<MinimalDataset[]>({
    key: () => ['datasets', tenantName.value],
    staleTime: minutesToMilliseconds(5),
    enabled: computed(() => !!tenantName.value),
    query: async () => {
      return await getDatasets({
        composable: '$fetch',
        path: { tenant_id: tenantName.value! },
      })
    },
  })
  return {
    datasets,
    datasetsAreLoading,
  }
})
