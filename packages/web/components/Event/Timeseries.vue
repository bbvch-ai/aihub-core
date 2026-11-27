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

const DENSE_BUCKET_COUNT = 31
const Y_AXIS_HEADROOM = 0.1
const SMALLEST_SHOWN_PERCENTAGE = 0.1

const formatShareOfTotal = (value: number, total: number): string => {
  if (total <= 0) {
    return '0%'
  }
  const percentage = value / total * 100
  if (percentage > 0 && percentage < SMALLEST_SHOWN_PERCENTAGE) {
    return `<${SMALLEST_SHOWN_PERCENTAGE}%`
  }
  return `${Number(percentage.toFixed(1))}%`
}

const largestBucketTotal = (bucketCount: number): number => {
  let largest = 0
  for (let index = 0; index < bucketCount; index++) {
    const total = chartSeries.value.reduce((sum, series) => sum + (series.data[index] ?? 0), 0)
    largest = Math.max(largest, total)
  }
  return largest
}

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

  const isSingleSeries = chartSeries.value.length <= 1
  const largestTotal = largestBucketTotal(buckets.length)
  const labelFontSize = buckets.length > DENSE_BUCKET_COUNT ? 10 : 13
  const labelColor = isDark.value ? 'var(--p-surface-200)' : 'var(--p-surface-800)'
  const { max: yAxisMax, tickAmount } = niceAxisScale(largestTotal, Y_AXIS_HEADROOM)
  const seriesTotals = chartSeries.value.map(series => series.data.reduce((sum, value) => sum + value, 0))

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
        // A single series' values are in the tooltip, where they never collide with each other.
        dataLabels: {
          total: {
            enabled: !isSingleSeries,
            style: { fontSize: `${labelFontSize}px`, fontWeight: 900, color: labelColor },
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
          chart: { offsetY: 0 },
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
        // ApexCharts' default weight of 900 at 11px smears once the title is rotated, worst on Windows' subpixel
        // font smoothing.
        style: { fontSize: '12px', fontWeight: 600 },
      },
      min: 0,
      max: yAxisMax,
      tickAmount,
      labels: {
        formatter: (value: number) => Number.isInteger(value) ? String(value) : '',
      },
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
      y: {
        formatter: (value: number, { seriesIndex }: { seriesIndex: number }) =>
          `${value} (${formatShareOfTotal(value, seriesTotals[seriesIndex] ?? 0)})`,
        title: {
          formatter: (seriesName: string) => isSingleSeries ? '' : `${seriesName}:`,
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
