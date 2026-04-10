import { type FullProcessInstanceDtoReadable, getProcessInstance } from '@core/sdk/client'
import { minutesToMilliseconds } from 'date-fns'
import { useRoute } from 'vue-router'

export const useProcessInstance = defineQuery(() => {
  const route = useRoute()
  const { tenantId } = useTenant()

  const { data: processInstance, isPending: processInstanceIsLoading } = useQuery<FullProcessInstanceDtoReadable>({
    key: () => ['tenant', tenantId.value, 'process-instances', route.params.process_class as string, route.params.process_id as string],
    staleTime: minutesToMilliseconds(5),
    enabled: useTenantReady('process_id', 'process_class'),
    query: async () => {
      return await getProcessInstance({
        composable: '$fetch',
        path: {
          tenant_id: tenantId.value!,
          process_id: route.params.process_id as string,
          process_class: route.params.process_class as string,
        },
      })
    },
  })
  return {
    processInstance,
    processInstanceIsLoading,
  }
})
