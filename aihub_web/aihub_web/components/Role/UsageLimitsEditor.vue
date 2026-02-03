<template>
  <div class="flex flex-col gap-3 rounded-lg border border-surface-200 p-4 dark:border-surface-700">
    <div class="flex items-center justify-between">
      <span class="font-semibold">{{ t('role.usage_limits') }}</span>
      <div class="flex items-center gap-2">
        <label
          for="unlimited"
          class="text-sm"
        >{{ t('role.unlimited') }}</label>
        <ToggleSwitch
          v-model="isUnlimited"
          input-id="unlimited"
        />
      </div>
    </div>

    <div
      v-if="!isUnlimited"
      class="flex flex-col gap-3"
    >
      <table class="w-full text-sm">
        <colgroup>
          <col>
          <col style="width: 6rem;">
          <col style="width: 6rem;">
          <col style="width: 3rem;">
        </colgroup>
        <thead>
          <tr>
            <th class="py-2 text-start font-medium">
              {{ t('role.usage_pattern') }}
            </th>
            <th class="py-2 text-start font-medium">
              {{ t('role.usage_limit_value') }}
            </th>
            <th class="py-2 text-start font-medium">
              {{ t('role.usage_period') }}
            </th>
            <th />
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="(ul, index) in limits"
            :key="`${ul.pattern}-${ul.period}-${index}`"
            class="border-b border-surface-200 dark:border-surface-700"
          >
            <td class="py-2">
              <Badge
                :value="ul.pattern"
                severity="secondary"
                class="border border-gray-400/30"
              />
            </td>
            <td class="py-2">
              {{ ul.limit }} {{ t('role.calls_per') }}
            </td>
            <td class="py-2">
              {{ getPeriodLabel(ul.period) }}
            </td>
            <td class="py-2 text-end">
              <Button
                icon="pi pi-times"
                severity="secondary"
                variant="text"
                rounded
                size="small"
                @click="remove(ul.pattern, ul.period)"
              />
            </td>
          </tr>
        </tbody>
        <tfoot>
          <tr>
            <td class="py-2">
              <div class="flex items-center">
                <span class="whitespace-nowrap rounded-l border border-r-0 border-surface-300 bg-surface-100 px-2 py-1.5 text-xs text-muted-color dark:border-surface-600 dark:bg-surface-800">
                  {{ AGENT_PREFIX }}
                </span>
                <InputText
                  v-model="newPattern"
                  placeholder=">"
                  size="small"
                  class="w-full rounded-l-none"
                />
              </div>
            </td>
            <td class="py-2">
              <InputText
                v-model.number="newLimit"
                type="number"
                min="1"
                :placeholder="t('role.usage_limit_value')"
                size="small"
                class="w-full"
              />
            </td>
            <td class="py-2">
              <select
                v-model="newPeriod"
                class="w-full rounded border border-surface-300 bg-surface-0 px-2 py-1.5 text-sm dark:border-surface-600 dark:bg-surface-900"
              >
                <option
                  v-for="opt in periodOptions"
                  :key="opt.value"
                  :value="opt.value"
                >
                  {{ opt.label }}
                </option>
              </select>
            </td>
            <td class="py-2 text-end">
              <Button
                type="button"
                icon="pi pi-plus"
                :label="t('role.add_button')"
                size="small"
                :disabled="!canAdd"
                @click="add"
              />
            </td>
          </tr>
        </tfoot>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'

import type { UsageLimitDTO } from '@core/sdk/client'

const { t } = useI18n()

const AGENT_PREFIX = 'aihub.user.agent.'
const PERIOD_VALUES = ['1h', '1d', '7d', '1mo'] as const

const limits = defineModel<UsageLimitDTO[]>('limits', { required: true })

const isUnlimited = computed({
  get: () => limits.value.length === 0,
  set: (val: boolean) => {
    if (val) {
      limits.value = []
    }
  },
})

const periodOptions = computed(() =>
  PERIOD_VALUES.map(value => ({ value, label: t(`period.${value}`) })),
)

const getPeriodLabel = (period: string): string => t(`period.${period}`)

const newPattern = ref('>')
const newLimit = ref<number>(100)
const newPeriod = ref<string>('1d')

const canAdd = computed(() => {
  if (!newPattern.value || !newLimit.value || newLimit.value < 1 || !newPeriod.value) {
    return false
  }
  const fullPattern = `${AGENT_PREFIX}${newPattern.value}`
  return !limits.value.some(ul => ul.pattern === fullPattern && ul.period === newPeriod.value)
})

const add = () => {
  if (!canAdd.value) return
  const fullPattern = `${AGENT_PREFIX}${newPattern.value}`
  limits.value.push({ pattern: fullPattern, limit: newLimit.value, period: newPeriod.value })
  newPattern.value = '>'
  newLimit.value = 100
  newPeriod.value = '1d'
}

const remove = (pattern: string, period: string) => {
  limits.value = limits.value.filter(ul => !(ul.pattern === pattern && ul.period === period))
}
</script>
