import { type FullProcessInstanceDtoReadable, getProcessInstance } from '@core/sdk/client'
import { minutesToMilliseconds } from 'date-fns'
import { useRoute } from 'vue-router'

export const useProcessInstance = defineQuery(() => {
  const route = useRoute()
  const { tenantName } = useTenantFromRoute()
  const isRouteReady = useRouteReady('process_id', 'process_class')

  const { data: processInstance, isPending: processInstanceIsLoading } = useQuery<FullProcessInstanceDtoReadable>({
    key: () => ['process-instances', tenantName.value, route.params.process_class as string, route.params.process_id as string],
    staleTime: minutesToMilliseconds(5),
    enabled: computed(() => isRouteReady.value && !!tenantName.value),
    query: async () => {
      return await getProcessInstance({
        composable: '$fetch',
        path: {
          tenant_id: tenantName.value!,
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
