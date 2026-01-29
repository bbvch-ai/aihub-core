<template>
  <div
    v-if="usage"
    class="flex flex-col gap-2"
  >
    <template v-if="usage.limits && usage.limits.length > 0">
      <div
        v-for="(limitStatus, index) in usage.limits"
        :key="index"
        class="flex flex-col gap-1"
      >
        <div class="flex justify-between items-center">
          <span class="text-sm font-medium">{{ t('usage.title') }}</span>
          <span
            v-if="limitStatus.reset_at"
            class="text-xs text-muted-color"
          >
            {{ t('usage.resets_at', { time: formatResetTime(limitStatus.reset_at) }) }}
          </span>
        </div>

        <ProgressBar
          :value="getProgress(limitStatus)"
          :show-value="false"
          :class="{ 'p-progressbar-warn': isNear(limitStatus), 'p-progressbar-danger': limitStatus.is_exceeded }"
        />
        <span class="text-sm">
          {{ t('usage.calls_remaining', { current: limitStatus.current_count, limit: limitStatus.limit }) }}
          <span class="text-xs text-muted-color">({{ limitStatus.period }})</span>
        </span>
      </div>

      <Message
        v-if="usage.is_exceeded"
        severity="error"
        :closable="false"
      >
        <span class="font-medium">{{ t('usage.limit_exceeded') }}</span>
        <span
          v-if="earliestReset"
          class="block text-sm"
        >
          {{ t('usage.limit_exceeded_detail', { time: formatResetTime(earliestReset) }) }}
        </span>
      </Message>
    </template>
    <template v-else>
      <span class="text-sm text-muted-color">{{ t('usage.unlimited_calls') }}</span>
    </template>
  </div>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { formatDistanceToNow } from 'date-fns'

import type { UsageStatusDto } from '@core/sdk/client'

const { t } = useI18n()

const props = defineProps<{
  usage: UsageStatusDto | null | undefined
}>()

interface LimitStatus {
  current_count: number
  limit: number
  period: string
  reset_at: string | Date | null
  is_exceeded: boolean
}

const getProgress = (ls: LimitStatus) => {
  return Math.min(100, (ls.current_count / ls.limit) * 100)
}

const isNear = (ls: LimitStatus) => {
  return ls.current_count >= ls.limit * 0.8 && !ls.is_exceeded
}

const earliestReset = computed(() => {
  if (!props.usage?.limits) return null
  const exceeded = props.usage.limits.filter((ls: LimitStatus) => ls.is_exceeded && ls.reset_at)
  if (exceeded.length === 0) return null
  return exceeded.reduce((earliest: LimitStatus, ls: LimitStatus) => {
    const eDate = typeof earliest.reset_at === 'string' ? new Date(earliest.reset_at) : earliest.reset_at
    const lDate = typeof ls.reset_at === 'string' ? new Date(ls.reset_at) : ls.reset_at
    if (!eDate) return ls
    if (!lDate) return earliest
    return lDate < eDate ? ls : earliest
  }).reset_at
})

const formatResetTime = (resetAt: string | Date) => {
  const date = typeof resetAt === 'string' ? new Date(resetAt) : resetAt
  return formatDistanceToNow(date, { addSuffix: true })
}
</script>

<style scoped>
:deep(.p-progressbar-warn .p-progressbar-value) {
  background: var(--p-yellow-500);
}

:deep(.p-progressbar-danger .p-progressbar-value) {
  background: var(--p-red-500);
}
</style>
