import {
  type EventTimeseries,
  getAgentEventTimeseries,
} from '@core/sdk/client'
import { minutesToMilliseconds } from 'date-fns'
import { useRoute } from 'vue-router'

export const useEventTimeseries = ({ eventName, timeRange, agentClass, agentId }: { eventName?: string, timeRange: Ref<string>, agentClass?: string, agentId?: string }) => {
  const route = useRoute()
  const { tenantId } = useTenant()

  const query = {
    agent_class: agentClass ?? route?.params?.agent_class,
    agent_id: agentId ?? route?.params?.agent_id,
    thread_id: route?.params?.thread_id,
    event_name: eventName,
  }
  const { data: timeseries, isPending: timeseriesIsLoading } = useQuery<EventTimeseries>({
    key: () => ['tenant', tenantId.value, 'events', 'agents', 'timeseries', timeRange.value, query],
    staleTime: minutesToMilliseconds(5),
    enabled: useTenantReady(),
    query: async () => {
      return await getAgentEventTimeseries({
        composable: '$fetch',
        path: {
          tenant_id: tenantId.value!,
          time_range: timeRange.value,
        },
        query,
      })
    },
  })

  return {
    timeseries,
    timeseriesIsLoading,
    timeRange,
  }
}
