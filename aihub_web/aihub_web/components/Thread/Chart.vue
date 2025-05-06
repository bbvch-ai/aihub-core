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

import type { ThreadDto, ThreadTimeStatisticsDto, EventBucket } from '@core/sdk/client' // Adjust path as needed
import type { ApexOptions } from 'apexcharts'

const props = defineProps<{
  statistics: ThreadTimeStatisticsDto
  thread: ThreadDto
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
      const date = new Date(value) // value is the ISO string from categories
      const dataPointIndex = opts?.dataPointIndex ?? 0

      let maxLabels = 10
      if (time_range === '1h') maxLabels = 12 // e.g., every 5 minutes
      else if (time_range === '24h') maxLabels = 8 // e.g., every 3 hours

      const totalDataPoints = categories.length
      const skipInterval = Math.max(1, Math.ceil(totalDataPoints / maxLabels))

      // Always show the first and last label if possible
      if (dataPointIndex === 0 || dataPointIndex === totalDataPoints - 1) {
        // Proceed to formatting
      }
      else if (dataPointIndex % skipInterval !== 0) {
        return '' // Skip this label
      }

      if (time_range === '1h' || time_range === '24h') {
        // European/Swiss format: HH:mm or HH:mm:ss for 1h/24h
        const options: Intl.DateTimeFormatOptions = {
          hour: '2-digit',
          minute: '2-digit',
          hour12: false, // Crucial for 24h format
        }
        return date.toLocaleTimeString('de-CH', options)
      }
      else {
        // For 30d, show e.g., "May 01" or "01. Mai"
        return date.toLocaleDateString('de-CH', { month: 'short', day: '2-digit' })
      }
      // Default fallback (should ideally be covered by above)
      return date.toLocaleDateString('de-CH')
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
        formatter: function (value: number) {
          // Show only integer values and if value is > 0 or it's 0 itself.
          if (Number.isInteger(value)) {
            return String(value)
          }
          return ''
        },
      },
      // Ensure y-axis ticks are integers if possible
      tickAmount: 5, // Or let ApexCharts decide by removing this
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
        formatter: function (value: string, { series, seriesIndex, dataPointIndex, w }) {
          // 'value' here is the category (ISO string from categories array)
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

<style scoped>
</style>
