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
          rows="5"
          cols="30"
          class="w-full"
        />
        <label for="in_label_description">
          {{ t('role.description') }}
        </label>
      </FloatLabel>
    </div>

    <!-- Agent Limits Section -->
    <div class="border-t pt-4">
      <h3 class="mb-3 text-lg font-semibold">
        {{ t('role.agent_limits') }}
      </h3>
      <div class="flex flex-col gap-3">
        <div class="flex flex-col gap-1">
          <label
            for="agent_calls_limit"
            class="text-sm font-medium"
          >
            {{ t('role.agent_calls_limit') }}
          </label>
          <InputNumber
            id="agent_calls_limit"
            v-model="role.agent_calls_limit"
            :placeholder="t('role.unlimited')"
            :min="0"
            class="w-full"
            show-buttons
          />
          <small class="text-surface-500">
            {{ t('role.agent_calls_limit_help') }}
          </small>
        </div>
        <div class="flex flex-col gap-1">
          <label
            for="agent_calls_period"
            class="text-sm font-medium"
          >
            {{ t('role.agent_calls_period') }}
          </label>
          <Select
            id="agent_calls_period"
            v-model="role.agent_calls_period"
            :options="periodOptions"
            option-label="label"
            option-value="value"
            class="w-full"
          />
          <small class="text-surface-500">
            {{ t('role.agent_calls_period_help') }}
          </small>
        </div>
      </div>
    </div>

    <DataTable
      :value="accessRules"
      data-key="id"
    >
      <Column
        field="accessRule"
        :header="t('role.access_rules')"
      >
        <template #body="{ data }">
          <Badge
            :value="data.accessRule"
            severity="secondary"
            class="border border-gray-400/30"
          />
        </template>
      </Column>
      <Column
        class="w-24 !text-end"
      >
        <template #body="{ data }">
          <Tag
            v-if="isNewAccessRule(data.accessRule)"
            :value="t('role.is_new')"
            severity="success"
          />
        </template>
      </Column>
      <Column
        class="w-12"
      >
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
    <div class="flex gap-2">
      <InputGroup>
        <InputGroupAddon>
          <i class="pi pi-lock-open" />
        </InputGroupAddon>
        <InputText
          v-model="newRule"
          :placeholder="t('role.add_access_role')"
          @click.enter="addRule"
        />
      </InputGroup>
      <div>
        <Button
          type="button"
          :label="t('role.add_button')"
          icon="pi pi-plus"
          :disabled="!newRule"
          @click="addRule"
        />
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
const role = ref<RoleResponse | CreateRoleRequest>({
  ...props.modelValue,
  agent_calls_period: props.modelValue.agent_calls_period ?? '1mo',
})

const periodOptions = [
  { label: '1 Hour', value: '1h' },
  { label: '1 Day', value: '1d' },
  { label: '1 Week', value: '7d' },
  { label: '1 Month', value: '1mo' },
]

watch(() => props.modelValue, (newValue) => {
  role.value = {
    ...newValue,
    agent_calls_period: newValue.agent_calls_period ?? '1mo',
  }
}, { deep: true })

const accessRules = computed(() => {
  return role.value.access_rules?.map((accessRule: string) => {
    return {
      accessRule,
      id: accessRule,
    }
  }) || []
})

const newRule = ref<string>('')

watch(() => [
  role.value.name,
  role.value.description,
  JSON.stringify(role.value.access_rules),
  role.value.agent_calls_limit,
  role.value.agent_calls_period,
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
