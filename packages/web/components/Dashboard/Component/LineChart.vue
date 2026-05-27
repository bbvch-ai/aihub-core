<template>
  <div class="relative">
    <div class="flex flex-col gap-1">
      <div class="flex gap-4">
        <p class="text-lg font-medium">
          {{ title }}
        </p>
        <DashboardTrend :timeseries="timeseries" />
      </div>
      <p
        class="text-surface-500"
      >
        {{ agentName }}
      </p>
    </div>
    <ClientOnly>
      <div class="absolute inset-x-0 top-0">
        <VueApexChart
          v-if="chartSeries && chartOptions"
          type="area"
          height="250px"
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
      height: '250px',
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
