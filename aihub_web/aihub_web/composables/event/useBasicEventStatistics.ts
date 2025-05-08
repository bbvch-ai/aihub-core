import { useRouteQuery } from '@vueuse/router'

import type { EventChartInput } from '@core/types/EventChartInput'

export const useBasicEventStatistics = () => {
  const timeRange = useRouteQuery<'1h' | '24h' | '30d' | '365d'>('range', '30d')
  const { timeseries: startSeries, timeseriesIsLoading: startIsLoading } = useEventTimeseries({
    eventName: 'StartEvent',
    timeRange,
  })

  const { timeseries: allSeries, timeseriesIsLoading: allIsLoading } = useEventTimeseries({
    timeRange,
  })

  const { timeseries: stopSeries, timeseriesIsLoading: stopIsLoading } = useEventTimeseries({
    eventName: 'StopEvent',
    timeRange,
  })

  const { timeseries: hitlSeries, timeseriesIsLoading: hitlIsLoading } = useEventTimeseries({
    eventName: 'HumanInTheLoopRequestEvent',
    timeRange,
  })

  const { timeseries: bitlSeries, timeseriesIsLoading: bitlIsLoading } = useEventTimeseries({
    eventName: 'BotInTheLoopRequestEvent',
    timeRange,
  })

  const { timeseries: aitlSeries, timeseriesIsLoading: aitlIsLoading } = useEventTimeseries({
    eventName: 'AgentInTheLoopRequestEvent',
    timeRange,
  })

  const { timeseries: exceptionSeries, timeseriesIsLoading: exstepsionIsLoading } = useEventTimeseries({
    eventName: 'ExceptionEvent',
    timeRange,
  })

  const charts = computed<EventChartInput[]>(() => [
    {
      title: 'Agent Invocations',
      isLoading: startIsLoading.value,
      timeseriesInputs: [
        { name: 'Agent Start', color: 'var(--p-surface-600)', timeseries: startSeries.value },
      ],
    },
    {
      title: 'End Events',
      isLoading: stopIsLoading.value || exstepsionIsLoading.value || hitlIsLoading.value || bitlIsLoading.value,
      timeseriesInputs: [
        { name: 'Success', color: 'var(--p-green-600)', timeseries: stopSeries.value },
        { name: 'Open (Human in the loop)', color: 'var(--p-yellow-500)', timeseries: hitlSeries.value },
        { name: 'Open (Bot in the Loop)', color: 'var(--p-yellow-600)', timeseries: bitlSeries.value },
        { name: 'Error', color: 'var(--p-red-600)', timeseries: exceptionSeries.value },
      ],
    },
    {
      title: 'Delegations',
      isLoading: aitlIsLoading.value,
      timeseriesInputs: [
        { name: 'Delegated Task (Agent in the Loop)', color: 'var(--p-blue-600)', timeseries: aitlSeries.value },
      ],
    },
    {
      title: 'All Events',
      isLoading: allIsLoading.value,
      timeseriesInputs: [
        { name: 'All Events', color: 'var(--p-surface-600)', timeseries: allSeries.value },
      ],
    },
  ])
  return {
    timeRange,
    charts,
  }
}
