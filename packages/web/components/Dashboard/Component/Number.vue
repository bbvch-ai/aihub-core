<template>
  <div class="pointer-events-none relative w-full [container-type:inline-size]">
    <p
      v-tooltip.top="isCompact ? exactSum : undefined"
      class="pointer-events-auto -mt-8 w-full whitespace-nowrap text-center font-medium leading-[18rem] opacity-70"
      :style="{ fontSize }"
    >
      {{ displayedSum }}
    </p>
    <DashboardTruncatedText
      :text="title"
      class="pointer-events-auto absolute bottom-8 w-full px-2 text-center text-lg font-bold opacity-80"
    />
    <DashboardTruncatedText
      :text="agentName"
      class="pointer-events-auto absolute bottom-2 w-full px-2 text-center text-surface-500"
    />
    <div class="absolute -bottom-6 flex w-full justify-center px-2">
      <DashboardTrend
        class="pointer-events-auto"
        :timeseries="timeseries"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import type { EventTimeseries } from '@core/sdk/client'
import type { DashboardWidget } from '@core/types/DashboardWidget'

const props = defineProps<{
  title: string
  timeseries: EventTimeseries
  widgetData: DashboardWidget
}>()

const COMPACT_THRESHOLD = 10_000
// A glyph of this font is at most ~0.6em wide, so 150cqi spread over the characters keeps the value within ~90% of the card.
const CARD_WIDTH_PER_CHARACTER = 150

const { formatNumber } = useNumberLocale()

const { sum } = useEventTimeseriesStats(props.timeseries)

const { agentName } = useAgentNameFromDashboardWidget(props.widgetData)

const isCompact = computed(() => sum.value >= COMPACT_THRESHOLD)
const exactSum = computed(() => formatNumber(sum.value))
const displayedSum = computed(() => isCompact.value
  ? formatNumber(sum.value, { notation: 'compact', maximumFractionDigits: 1 })
  : exactSum.value)
const fontSize = computed(() => `min(12rem, ${CARD_WIDTH_PER_CHARACTER / displayedSum.value.length}cqi)`)
</script>
