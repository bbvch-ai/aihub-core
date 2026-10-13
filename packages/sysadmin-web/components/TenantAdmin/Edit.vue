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

    <FormKit
      v-model="tenant.chat_disclaimer"
      type="localeInput"
      name="chat_disclaimer"
      input-type="textarea"
      :allow-translation="false"
      :label="t('tenant_admin.form.chat_disclaimer')"
      :help="t('tenant_admin.form.chat_disclaimer_help')"
      :placeholder="{ en: t('tenant_admin.form.chat_disclaimer') }"
      validation="localeRequired|disclaimerLength"
      :validation-rules="{ disclaimerLength }"
      :validation-messages="{ disclaimerLength: t('tenant_admin.form.chat_disclaimer_too_long') }"
    />

    <AccessRulesEditor
      v-model:rules="accessRules"
      :initial-rules="initialAccessRules"
      :restrict-to-tenant="false"
    />
  </div>
</template>

<script setup lang="ts">
import AccessRulesEditor from '@core/components/Role/AccessRulesEditor.vue'

import type { TenantResponse, UpdateTenantMetadataRequest } from '~/sdk/client'

type EditableTenant = TenantResponse | UpdateTenantMetadataRequest

const { t } = useI18n()

const props = defineProps<{
  modelValue: EditableTenant
}>()

const emit = defineEmits<{
  'update:modelValue': [EditableTenant]
}>()

const initialAccessRules = ref<string[]>([...(props.modelValue.access_rules ?? [])])
const tenant = ref<EditableTenant>(props.modelValue)

function disclaimerLength(node: { value: unknown }) {
  return Object.values((node.value ?? {}) as Record<string, string | null>)
    .every(value => !value || [...value.trim()].length <= 100)
}

watch(() => props.modelValue, (newValue) => {
  tenant.value = newValue
}, { deep: true })

const accessRules = computed({
  get: () => tenant.value.access_rules ?? [],
  set: (val) => { tenant.value.access_rules = val },
})

watch(tenant, (value) => {
  emit('update:modelValue', value)
}, { deep: true })
</script>
