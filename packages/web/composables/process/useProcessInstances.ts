import { type FullProcessInstanceDtoReadable, getAllProcessInstances } from '@core/sdk/client'
import { minutesToMilliseconds } from 'date-fns'

export type FullProcessInstanceDto = FullProcessInstanceDtoReadable

export const useProcessInstances = defineQuery((options?: { online?: boolean }) => {
  const { tenantId } = useTenant()

  const { data: processInstances, isPending: processInstancesAreLoading } = useQuery<FullProcessInstanceDto[]>({
    key: () => ['tenant', tenantId.value, 'process-instances', options?.online],
    staleTime: minutesToMilliseconds(5),
    enabled: useTenantReady(),
    query: async () => {
      return await getAllProcessInstances({
        composable: '$fetch',
        path: { tenant_id: tenantId.value! },
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
