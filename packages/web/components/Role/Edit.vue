<template>
  <div class="flex flex-col gap-4">
    <div class="flex flex-col gap-2">
      <div class="flex flex-col gap-1">
        <FloatLabel variant="in">
          <InputText
            id="in_label_name"
            v-model="role.name"
            :maxlength="nameMaxLength"
            rows="5"
            cols="30"
            class="w-full"
            :disabled="nameReadonly"
          />
          <label for="in_label_name">
            {{ t('role.name') }}
          </label>
        </FloatLabel>
        <small
          v-if="nameReadonly"
          class="text-surface-500"
        >
          {{ t('role.name_immutable_hint') }}
        </small>
      </div>
      <FloatLabel variant="in">
        <Textarea
          id="in_label_description"
          v-model="role.description"
          :maxlength="descriptionMaxLength"
          rows="3"
          cols="30"
          class="w-full"
        />
        <label for="in_label_description">
          {{ t('role.description') }}
        </label>
      </FloatLabel>
    </div>

    <AccessRulesEditor
      v-model:rules="accessRules"
      :initial-rules="initialAccessRules"
    />

    <UsageLimitsEditor v-model:limits="usageLimits" />
  </div>
</template>

<script setup lang="ts">
import { CreateRoleRequestSchema } from '@core/sdk/client/schemas.gen'
import { useI18n } from 'vue-i18n'

import AccessRulesEditor from './AccessRulesEditor.vue'
import UsageLimitsEditor from './UsageLimitsEditor.vue'

import type { CreateRoleRequest, RoleResponse } from '@core/sdk/client'

const { t } = useI18n()

const nameMaxLength = schemaMaxLength(CreateRoleRequestSchema, 'name')
const descriptionMaxLength = schemaMaxLength(CreateRoleRequestSchema, 'description')

const props = defineProps<{
  modelValue: RoleResponse | CreateRoleRequest
  nameReadonly?: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [RoleResponse | CreateRoleRequest]
}>()

const initialAccessRules = ref<string[]>([...(props.modelValue.access_rules ?? [])])
const role = ref<RoleResponse | CreateRoleRequest>(props.modelValue)

watch(() => props.modelValue, (newValue) => {
  role.value = newValue
}, { deep: true })

const accessRules = computed({
  get: () => role.value.access_rules ?? [],
  set: (val) => { role.value.access_rules = val },
})

const usageLimits = computed({
  get: () => role.value.usage_limits ?? [],
  set: (val) => { role.value.usage_limits = val },
})

watch(() => [
  role.value.name,
  role.value.description,
  JSON.stringify(role.value.access_rules),
  JSON.stringify(role.value.usage_limits),
], () => {
  emit('update:modelValue', role.value)
})
</script>
