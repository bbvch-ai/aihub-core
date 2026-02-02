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
            v-for="ul in limits"
            :key="ul.pattern"
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
              {{ periodLabelMap[ul.period] ?? ul.period }}
            </td>
            <td class="py-2 text-end">
              <Button
                icon="pi pi-times"
                severity="secondary"
                variant="text"
                rounded
                size="small"
                @click="remove(ul.pattern)"
              />
            </td>
          </tr>
        </tbody>
        <tfoot>
          <tr>
            <td class="py-2">
              <div class="flex items-center">
                <span class="whitespace-nowrap rounded-l border border-r-0 border-surface-300 bg-surface-100 px-2 py-1.5 text-xs text-muted-color dark:border-surface-600 dark:bg-surface-800">
                  aihub.user.agent.
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
                v-model.number="newLimitStr"
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
                :disabled="!newPattern || !newLimitStr || !newPeriod"
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

const limits = defineModel<UsageLimitDTO[]>('limits', { required: true })

const hasLimits = ref(!!limits.value.length)

const isUnlimited = computed({
  get: () => !hasLimits.value,
  set: (val: boolean) => {
    hasLimits.value = !val
    if (val) {
      limits.value = []
    }
  },
})

watch(() => limits.value.length, (len) => {
  hasLimits.value = !!len
})

const periodOptions = [
  { label: t('period.1h'), value: '1h' },
  { label: t('period.1d'), value: '1d' },
  { label: t('period.7d'), value: '7d' },
  { label: t('period.1mo'), value: '1mo' },
]

const periodLabelMap: Record<string, string> = {
  '1h': t('period.1h'),
  '1d': t('period.1d'),
  '7d': t('period.7d'),
  '1mo': t('period.1mo'),
}

const newPattern = ref('>')
const newLimitStr = ref<number | string>(100)
const newPeriod = ref('1d')

const add = () => {
  const limit = Number(newLimitStr.value)
  if (!newPattern.value || !limit || !newPeriod.value) return
  const fullPattern = `${AGENT_PREFIX}${newPattern.value}`
  const duplicate = limits.value.some(
    ul => ul.pattern === fullPattern && ul.period === newPeriod.value,
  )
  if (duplicate) return
  limits.value.push({ pattern: fullPattern, limit, period: newPeriod.value })
  newPattern.value = '>'
  newLimitStr.value = 100
  newPeriod.value = '1d'
}

const remove = (pattern: string) => {
  limits.value = limits.value.filter(ul => ul.pattern !== pattern)
}
</script>
