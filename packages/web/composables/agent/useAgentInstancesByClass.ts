import { type FullAgentInstanceDto, getAgentClassInstances } from '@core/sdk/client'
import { minutesToMilliseconds } from 'date-fns'

import type { MaybeRefOrGetter } from 'vue'

/**
 * Instances of an arbitrary agent class. Unlike `useAgentClassInstances`, the class comes from a
 * caller-supplied value rather than the route, so this is a plain composable with a reactive key
 * instead of a `defineQuery` singleton.
 */
export const useAgentInstancesByClass = (agentClass: MaybeRefOrGetter<string | null | undefined>) => {
  const { tenantId } = useTenant()
  const tenantReady = useTenantReady()

  const { data: agentInstances, isPending: agentInstancesAreLoading } = useQuery<FullAgentInstanceDto[]>({
    key: () => ['tenant', tenantId.value, 'agent-class-instances', toValue(agentClass) ?? ''],
    staleTime: minutesToMilliseconds(5),
    enabled: computed(() => tenantReady.value && !!toValue(agentClass)),
    query: async () => {
      return await getAgentClassInstances({
        composable: '$fetch',
        path: {
          tenant_id: tenantId.value!,
          agent_class: toValue(agentClass)!,
        },
      })
    },
  })

  return {
    agentInstances,
    agentInstancesAreLoading,
  }
}
