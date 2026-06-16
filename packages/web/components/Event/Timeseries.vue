<template>
  <ClientOnly>
    <VueApexChart
      class="w-full"
      type="bar"
      :height="height"
      :options="chartOptions"
      :series="chartSeries"
    />
  </ClientOnly>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import VueApexChart from 'vue3-apexcharts'

import type { EventBucket } from '@core/sdk/client'
import type { TimeseriesInput } from '@core/types/TimeseriesInput'
import type { ApexOptions } from 'apexcharts'

const props = withDefaults(defineProps<{
  title: string
  seriesInputs: TimeseriesInput[]
  height?: number
}>(), {
  height: 350,
})

const { t } = useI18n()
const isDark = useDarkMode()

const chartSeries = computed(() => {
  if (!props.seriesInputs || props.seriesInputs.length === 0) {
    return []
  }

  return props.seriesInputs
    .map(input => ({
      name: input.name,
      data: input.timeseries?.buckets?.map(bucket => bucket.total_events || 0) ?? [],
    }))
    .filter(series => series.data.some(value => value > 0))
})

const chartOptions = computed<ApexOptions>(() => {
  const representativeTimeseries = props.seriesInputs?.find(s => s.timeseries?.buckets?.length > 0)?.timeseries

  if (!representativeTimeseries) {
    // Fallback options if no data is available to derive categories, etc.
    return {
      chart: {
        type: 'bar',
        height: props.height,
        foreColor: isDark.value ? 'var(--p-surface-200)' : 'var(--p-surface-800)',
      },
      theme: {
        mode: isDark.value ? 'dark' : 'light',
      },
      noData: {
        text: t('chart.no_data'),
        align: 'center',
        verticalAlign: 'middle',
        style: {
          fontSize: '14px',
        },
      },
      yaxis: {
        title: {
          text: `# ${props.title}`,
        },
      },
      legend: {
        show: false,
      },
    }
  }

  const { buckets, time_range, resolution } = representativeTimeseries

  // Generate categories for the X-axis from bucket start times
  const categories = buckets.map((bucket: EventBucket) => {
    const date = new Date(bucket.start_time)
    return date.toISOString()
  })

  const activeSeriesColors = props.seriesInputs
    .filter(input =>
      input.timeseries.buckets.some(bucket => (bucket.total_events || 0) > 0) && input.color,
    )
    .map(input => input.color!)

  const getXAxisLabelFormatter = () => {
    return (value: string, _: string, opts?: { i?: number }) => {
      const date = new Date(value)
      const dataPointIndex = opts?.i ?? 0

      // Determine max labels based on time range to avoid clutter
      let maxLabels = 31 // For 1 month, all days have labels, for 1 year, each month has exactly 12 labels
      if (time_range === '1h') maxLabels = 12 // e.g., every 5 minutes for 1 hour
      else if (time_range === '24h') maxLabels = 8 // e.g., every 3 hours for 24 hours

      const totalDataPoints = categories.length
      const skipInterval = Math.max(1, Math.ceil(totalDataPoints / maxLabels))

      if (dataPointIndex % skipInterval !== 0 && dataPointIndex !== totalDataPoints - 1) {
        return ''
      }

      // Format date based on time range
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
      height: props.height,
      stacked: true,
      offsetY: 20,
      toolbar: {
        show: false,
      },
      zoom: {
        enabled: false,
      },
      foreColor: isDark.value ? 'var(--p-surface-200)' : 'var(--p-surface-800)',
    },
    plotOptions: {
      bar: {
        horizontal: false,
        columnWidth: resolution === '1m' ? '80%' : '50%',
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
        hideOverlappingLabels: false,
        trim: true,
        style: {
          fontSize: '10px',
        },
      },
    },
    yaxis: {
      title: {
        text: `# ${props.title}`,
        offsetX: 5,
      },
      min: 0,
      labels: {
        formatter: (value: number) => Number.isInteger(value) ? String(value) : '',
      },
      tickAmount: 5,
      forceNiceScale: true,
    },
    legend: {
      show: true,
      showForSingleSeries: true,
      position: 'top',
      offsetY: 35,
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
    colors: activeSeriesColors.length > 0 ? activeSeriesColors : undefined,
    noData: {
      text: t('chart.no_data'),
      align: 'center',
      verticalAlign: 'middle',
      style: {
        fontSize: '14px',
      },
    },
  }
})
</script>
