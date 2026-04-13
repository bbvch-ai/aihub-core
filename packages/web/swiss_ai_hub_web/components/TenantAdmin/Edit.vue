<template>
  <div class="flex flex-col gap-4">
    <div class="flex flex-col gap-2">
      <FloatLabel variant="in">
        <InputText
          id="tenant_name"
          v-model="tenant.name"
          class="w-full"
        />
        <label for="tenant_name">
          {{ t('tenant_admin.form.name') }}
        </label>
      </FloatLabel>
      <FloatLabel variant="in">
        <Textarea
          id="tenant_description"
          v-model="tenant.description"
          rows="3"
          class="w-full"
        />
        <label for="tenant_description">
          {{ t('tenant_admin.form.description') }}
        </label>
      </FloatLabel>
    </div>

    <AccessRulesEditor
      v-model:rules="accessRules"
      :initial-rules="initialAccessRules"
    />
  </div>
</template>

<script setup lang="ts">
import AccessRulesEditor from '@core/components/Role/AccessRulesEditor.vue'

import type { CreateTenantRequest, TenantResponse } from '@core/sdk/client'

const { t } = useI18n()

const props = defineProps<{
  modelValue: TenantResponse | CreateTenantRequest
}>()

const emit = defineEmits<{
  'update:modelValue': [TenantResponse | CreateTenantRequest]
}>()

const initialAccessRules = ref<string[]>([...(props.modelValue.access_rules ?? [])])
const tenant = ref<TenantResponse | CreateTenantRequest>(props.modelValue)

watch(() => props.modelValue, (newValue) => {
  tenant.value = newValue
}, { deep: true })

const accessRules = computed({
  get: () => tenant.value.access_rules ?? [],
  set: (val) => { tenant.value.access_rules = val },
})

watch(() => [
  tenant.value.name,
  tenant.value.description,
  JSON.stringify(tenant.value.access_rules),
], () => {
  emit('update:modelValue', tenant.value)
})
</script>
