import { type FullProcessInstanceDtoReadable, getAllProcessInstances } from '@core/sdk/client'
import { useQuery } from '@pinia/colada'
import { minutesToMilliseconds } from 'date-fns'

export type FullProcessInstanceDto = FullProcessInstanceDtoReadable

export const useProcessInstances = defineQuery((options?: { online?: boolean }) => {
  const { tenantName } = useTenant()

  const { data: processInstances, isPending: processInstancesAreLoading } = useQuery<FullProcessInstanceDto[]>({
    key: () => ['process-instances', tenantName.value, options?.online],
    staleTime: minutesToMilliseconds(5),
    enabled: computed(() => !!tenantName.value),
    query: async () => {
      return await getAllProcessInstances({
        composable: '$fetch',
        path: { tenant_id: tenantName.value! },
        query: {
          online: options?.online,
        },
      })
    },
  })
  return {
    processInstances,
    processInstancesAreLoading,
  }
})
