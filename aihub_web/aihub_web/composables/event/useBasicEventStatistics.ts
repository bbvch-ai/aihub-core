import type { EventChartInput } from '@core/types/EventChartInput'

import { useI18n } from '#imports'

export const useBasicEventStatistics = () => {
  const { t } = useI18n()

  const router = useRouter()
  const route = useRoute()
  const timeRange = useRouteQuery<'1h' | '24h' | '30d' | '365d'>('range', '30d', { route, router })

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
      title: t('event.statistics.charts.agentInvocations'),
      isLoading: startIsLoading.value,
      timeseriesInputs: [
        { name: t('event.statistics.charts.agentStart'), color: 'var(--p-surface-600)', timeseries: startSeries.value },
      ],
    },
    {
      title: t('event.statistics.charts.endEvents'),
      isLoading: stopIsLoading.value || exstepsionIsLoading.value || hitlIsLoading.value || bitlIsLoading.value,
      timeseriesInputs: [
        { name: t('event.statistics.charts.success'), color: 'var(--p-green-600)', timeseries: stopSeries.value },
        { name: t('event.statistics.charts.openHumanInTheLoop'), color: 'var(--p-yellow-500)', timeseries: hitlSeries.value },
        { name: t('event.statistics.charts.openBotInTheLoop'), color: 'var(--p-yellow-600)', timeseries: bitlSeries.value },
        { name: t('event.statistics.charts.error'), color: 'var(--p-red-600)', timeseries: exceptionSeries.value },
      ],
    },
    {
      title: t('event.statistics.charts.delegations'),
      isLoading: aitlIsLoading.value,
      timeseriesInputs: [
        { name: t('event.statistics.charts.delegatedTaskAgentInTheLoop'), color: 'var(--p-blue-600)', timeseries: aitlSeries.value },
      ],
    },
    {
      title: t('event.statistics.charts.allEvents'),
      isLoading: allIsLoading.value,
      timeseriesInputs: [
        { name: t('event.statistics.charts.allEvents'), color: 'var(--p-surface-600)', timeseries: allSeries.value },
      ],
    },
  ])
  return {
    timeRange,
    charts,
  }
}
