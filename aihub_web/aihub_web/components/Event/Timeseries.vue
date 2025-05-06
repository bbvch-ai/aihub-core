<template>
  <ClientOnly>
    <apexchart
      type="bar"
      height="350"
      :options="chartOptions"
      :series="chartSeries"
    />
  </ClientOnly>
</template>

<script setup lang="ts">
import { useDark } from '@vueuse/core'
import { computed } from 'vue'

import type { AgentEventTimeseries, EventBucket, ThreadEventTimeseries } from '@core/sdk/client'
import type { ApexOptions } from 'apexcharts'

const props = defineProps<{
  statistics: ThreadEventTimeseries | AgentEventTimeseries
  title: string
  bars: Array<{ key: keyof EventBucket, name: string, color?: string }>
}>()

const isDark = useDark({ storageKey: 'dark' })

const chartSeries = computed(() => {
  if (!props.statistics || !props.statistics.buckets || props.statistics.buckets.length === 0) {
    return []
  }

  return props.bars.map(eventType => ({
    name: eventType.name,
    data: props.statistics.buckets.map(bucket => bucket[eventType.key] || 0),
  })).filter(series => series.data.some(value => value > 0))
})

const chartOptions = computed<ApexOptions>(() => {
  const { buckets, time_range, resolution } = props.statistics

  const categories = buckets.map((bucket) => {
    const date = new Date(bucket.start_time)
    return date.toISOString()
  })

  const seriesColors = props.bars
    .filter(eventType =>
      buckets.some(bucket => (bucket[eventType.key] || 0) > 0),
    )
    .map(eventType => eventType.color).filter(color => color !== undefined) as string[]

  const getXAxisLabelFormatter = () => {
    return function (value: string, timestamp?: number, opts?: { dataPointIndex?: number }) {
      const date = new Date(value)
      const dataPointIndex = opts?.dataPointIndex ?? 0

      let maxLabels = 10
      if (time_range === '1h') maxLabels = 12
      else if (time_range === '24h') maxLabels = 8

      const totalDataPoints = categories.length
      const skipInterval = Math.max(1, Math.ceil(totalDataPoints / maxLabels))

      if (dataPointIndex % skipInterval !== 0) {
        return '' // Skip this label
      }

      if (time_range === '1h' || time_range === '24h') {
        const options: Intl.DateTimeFormatOptions = {
          hour: '2-digit',
          minute: '2-digit',
          hour12: false,
        }
        return date.toLocaleTimeString('de-CH', options)
      }
      return date.toLocaleDateString('de-CH', { month: 'short', day: '2-digit' })
    }
  }

  return {
    chart: {
      type: 'bar',
      height: 350,
      stacked: true,
      toolbar: {
        show: false,
      },
      zoom: {
        enabled: true,
      },
      foreColor: isDark.value ? 'var(--p-surface-200)' : 'var(--p-surface-800)',
    },
    theme: {
      mode: isDark.value,
    },
    plotOptions: {
      bar: {
        horizontal: false,
        columnWidth: resolution === '1m' ? '80%' : resolution === '1h' ? '70%' : '50%',
        dataLabels: {
          total: {
            enabled: true,
            style: {
              fontSize: '13px',
              fontWeight: 900,
              color: isDark.value ? 'var(--p-surface-200)' : 'var(--p-surface-800)',
            },
          },
        },
      },
    },
    dataLabels: {
      enabled: false,
    },
    responsive: [
      {
        breakpoint: 480,
        options: {
          legend: {
            position: 'bottom',
            offsetX: -10,
            offsetY: 0,
          },
        },
      },
    ],
    xaxis: {
      type: 'category',
      categories: categories,
      labels: {
        formatter: getXAxisLabelFormatter(),
        rotate: -45,
        rotateAlways: true,
        hideOverlappingLabels: true,
        trim: true,
        style: {
          fontSize: '10px',
        },
      },
    },
    yaxis: {
      title: {
        text: `# ${props.title}`,
      },
      min: 0,
      labels: {
        formatter: (value: number) => Number.isInteger(value) ? String(value) : '',
      },
      tickAmount: 5,
      forceNiceScale: true,
    },
    legend: {
      position: 'top',
      offsetY: 0,
    },
    fill: {
      opacity: 1,
    },
    tooltip: {
      theme: isDark.value ? 'dark' : 'light',
      x: {
        formatter: (value: string) => {
          const date = new Date(value)
          if (time_range === '1h' || time_range === '24h') {
            return date.toLocaleString('de-CH', { dateStyle: 'medium', timeStyle: 'medium', hour12: false })
          }
          return date.toLocaleDateString('de-CH', { weekday: 'short', year: 'numeric', month: 'short', day: 'numeric' })
        },
      },
    },
    colors: seriesColors.length > 0 ? seriesColors : undefined,
    noData: {
      text: 'No data available for this period.',
      align: 'center',
      verticalAlign: 'top',
      style: {
        fontSize: '14px',
      },
    },
  }
})
</script>
