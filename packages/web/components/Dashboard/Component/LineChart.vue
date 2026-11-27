<template>
  <div class="relative">
    <div
      ref="titleBlock"
      class="relative z-10 flex w-fit max-w-full flex-col gap-1"
    >
      <div class="flex min-w-0 gap-4">
        <DashboardTruncatedText
          tag="p"
          :text="title"
          class="min-w-0 text-lg font-medium"
        />
        <DashboardTrend
          class="shrink-0"
          :timeseries="timeseries"
        />
      </div>
      <DashboardTruncatedText
        tag="p"
        :text="agentName"
        class="text-surface-500"
      />
    </div>
    <ClientOnly>
      <div class="absolute inset-x-0 top-0">
        <VueApexChart
          v-if="chartSeries && chartOptions"
          type="area"
          :height="CHART_HEIGHT_PX"
          :options="chartOptions"
          :series="chartSeries"
        />
      </div>
    </ClientOnly>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import VueApexChart from 'vue3-apexcharts'

import type { EventTimeseries, EventBucket } from '@core/sdk/client'
import type { DashboardWidget } from '@core/types/DashboardWidget'
import type { ApexOptions } from 'apexcharts'

const props = defineProps<{
  title: string
  timeseries: EventTimeseries
  widgetData: DashboardWidget
}>()

const isDark = useDarkMode()
const { t } = useI18n()

const { agentName } = useAgentNameFromDashboardWidget(props.widgetData)

const CHART_HEIGHT_PX = 250
const PEAK_GAP_BELOW_TITLE_PX = 12

const titleBlock = ref<HTMLElement | null>(null)
const { height: titleBlockHeight } = useElementSize(titleBlock)

// The chart sits behind the title, so the axis is stretched until the highest peak ends below it.
const yAxisMax = computed(() => {
  const largestValue = Math.max(0, ...(props.timeseries?.buckets ?? []).map(bucket => bucket.total_events ?? 0))
  if (largestValue === 0) {
    return undefined
  }
  const reservedHeightPx = Math.min(CHART_HEIGHT_PX / 2, titleBlockHeight.value + PEAK_GAP_BELOW_TITLE_PX)
  return largestValue * CHART_HEIGHT_PX / (CHART_HEIGHT_PX - reservedHeightPx)
})

const chartSeries = computed(() => {
  if (!props.timeseries?.buckets?.length) {
    return [{ data: [] }]
  }
  return [{
    name: props.title || 'Events',
    data: props.timeseries.buckets.map((bucket: EventBucket) => ({
      x: new Date(bucket.start_time).getTime(),
      y: bucket.total_events ?? 0,
    })),
  }]
})

const chartOptions = computed<ApexOptions>(() => {
  const lineColor = isDark.value ? '#9CA3AF' : '#374151' // gray-400 for dark, gray-700 for light
  const gradientOpacityFrom = isDark.value ? 0.5 : 0.6
  const gradientOpacityTo = isDark.value ? 0.05 : 0.1

  return {
    colors: [lineColor],
    chart: {
      type: 'area',
      height: CHART_HEIGHT_PX,
      sparkline: {
        enabled: true,
      },
      animations: {
        enabled: true,
        easing: 'smooth',
        speed: 600,
        animateGradually: {
          enabled: true,
          delay: 100,
        },
        dynamicAnimation: {
          enabled: true,
          speed: 300,
        },
      },
    },
    yaxis: {
      show: false,
      min: 0,
      max: yAxisMax.value,
    },
    stroke: {
      curve: 'smooth',
      width: 2.5,
    },
    fill: {
      type: 'gradient',
      gradient: {
        shadeIntensity: isDark.value ? 0.7 : 1,
        opacityFrom: gradientOpacityFrom,
        opacityTo: gradientOpacityTo,
        // Removed stops for a linear gradient from opacityFrom to opacityTo
        // To make it more like the desired image where the top has more body:
        stops: [0, 85, 100], // Full opacityFrom for first 85% then fade
      },
    },
    tooltip: {
      enabled: true,
      theme: isDark.value ? 'dark' : 'light',
      style: {
        fontSize: '12px',
      },
      x: {
        show: true,
        format: 'dd MMM HH:mm',
      },
      y: {
        title: {
          formatter: (seriesName: string) => `${seriesName}: `,
        },
        formatter: (value: number) => {
          return String(Math.round(value))
        },
      },
      marker: {
        show: true,
      },
    },
    noData: {
      text: t('chart.no_data'),
      align: 'center',
      verticalAlign: 'middle',
      offsetX: 0,
      offsetY: 0,
      style: {
        fontSize: '12px',
      },
    },
  }
})
</script>
