<template>
  <div class="flex flex-col gap-4">
    <div class="flex flex-col gap-2">
      <FloatLabel variant="in">
        <InputText
          id="in_label_name"
          v-model="role.name"
          rows="5"
          cols="30"
          class="w-full"
        />
        <label for="in_label_name">
          {{ t('role.name') }}
        </label>
      </FloatLabel>
      <FloatLabel variant="in">
        <Textarea
          id="in_label_description"
          v-model="role.description"
          rows="3"
          cols="30"
          class="w-full"
        />
        <label for="in_label_description">
          {{ t('role.description') }}
        </label>
      </FloatLabel>
    </div>

    <!-- Access Rules -->
    <div class="flex flex-col gap-2 rounded-lg border border-surface-200 p-4 dark:border-surface-700">
      <span class="font-semibold">{{ t('role.access_rules') }}</span>
      <DataTable
        v-if="role.access_rules?.length"
        :value="accessRules"
        data-key="id"
        size="small"
      >
        <Column field="accessRule">
          <template #body="{ data }">
            <Badge
              :value="data.accessRule"
              severity="secondary"
              class="border border-gray-400/30"
            />
          </template>
        </Column>
        <Column class="w-24 !text-end">
          <template #body="{ data }">
            <Tag
              v-if="isNewAccessRule(data.accessRule)"
              :value="t('role.is_new')"
              severity="success"
            />
          </template>
        </Column>
        <Column class="w-12">
          <template #body="{ data }">
            <Button
              icon="pi pi-times"
              severity="secondary"
              variant="text"
              rounded
              size="small"
              @click="removeAccessRule(data.accessRule)"
            />
          </template>
        </Column>
      </DataTable>
      <span
        v-else
        class="text-sm italic text-muted-color"
      >
        {{ t('role.no_access_rules') }}
      </span>
      <div class="flex items-center gap-2">
        <InputText
          v-model="newRule"
          :placeholder="t('role.add_access_role')"
          size="small"
          class="flex-1"
          @keyup.enter="addRule"
        />
        <Button
          type="button"
          icon="pi pi-plus"
          size="small"
          :disabled="!newRule"
          @click="addRule"
        />
      </div>
    </div>

    <!-- Usage Limits -->
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
          <tbody>
            <tr
              v-for="ul in (role.usage_limits ?? [])"
              :key="ul.pattern"
              class="border-b border-surface-200 dark:border-surface-700"
            >
              <td class="py-2">
                <Badge
                  :value="displayPattern(ul.pattern)"
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
                  @click="removeUsageLimit(ul.pattern)"
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
                  size="small"
                  :disabled="!newPattern || !newLimitStr || !newPeriod"
                  @click="addUsageLimit"
                />
              </td>
            </tr>
          </tfoot>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'

import type { CreateRoleRequest, RoleResponse } from '@core/sdk/client'

const { t } = useI18n()

const props = defineProps<{
  modelValue: RoleResponse | CreateRoleRequest
}>()

const emit = defineEmits<{
  'update:modelValue': [RoleResponse | CreateRoleRequest]
}>()

const initialAccessRules = ref<string[]>([...(props.modelValue.access_rules ?? [])])
const role = ref<RoleResponse | CreateRoleRequest>(props.modelValue)

watch(() => props.modelValue, (newValue) => {
  role.value = newValue
  hasLimits.value = !!newValue.usage_limits?.length
}, { deep: true })

const accessRules = computed(() => {
  return role.value.access_rules?.map((accessRule: string) => ({
    accessRule,
    id: accessRule,
  })) || []
})

const newRule = ref<string>('')

const hasLimits = ref(!!props.modelValue.usage_limits?.length)

const isUnlimited = computed({
  get: () => !hasLimits.value,
  set: (val: boolean) => {
    hasLimits.value = !val
    if (val) {
      role.value.usage_limits = []
    }
  },
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

const AGENT_PREFIX = 'aihub.user.agent.'

const displayPattern = (pattern: string): string => {
  return pattern.startsWith(AGENT_PREFIX) ? pattern : `${AGENT_PREFIX}${pattern}`
}

const newPattern = ref('>')
const newLimitStr = ref<number | string>(100)
const newPeriod = ref('1d')

const addUsageLimit = () => {
  const limit = Number(newLimitStr.value)
  if (!newPattern.value || !limit || !newPeriod.value) return
  if (!role.value.usage_limits) {
    role.value.usage_limits = []
  }
  role.value.usage_limits.push({
    pattern: newPattern.value,
    limit,
    period: newPeriod.value,
  })
  newPattern.value = '>'
  newLimitStr.value = 100
  newPeriod.value = '1d'
}

const removeUsageLimit = (pattern: string) => {
  if (!role.value.usage_limits) return
  role.value.usage_limits = role.value.usage_limits.filter(
    ul => ul.pattern !== pattern,
  )
}

watch(() => [
  role.value.name,
  role.value.description,
  JSON.stringify(role.value.access_rules),
  JSON.stringify(role.value.usage_limits),
], () => {
  emit('update:modelValue', role.value)
})

const isNewAccessRule = (accessRule: string) => {
  return !initialAccessRules.value?.includes(accessRule)
}

const addRule = () => {
  if (!newRule.value) return
  if (!role.value.access_rules) {
    role.value.access_rules = []
  }
  role.value.access_rules.push(newRule.value)
  newRule.value = ''
}

const removeAccessRule = (accessRule: string) => {
  if (!role.value.access_rules) return
  role.value.access_rules = role.value.access_rules.filter(
    (rule: string) => rule !== accessRule,
  )
}
</script>

<style scoped>

</style>
