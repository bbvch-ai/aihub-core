<template>
  <div class="flex flex-col gap-4">
    <div class="flex flex-col gap-2">
      <FloatLabel variant="in">
        <InputText
          id="tenant_name"
          v-model="tenant.name"
          :maxlength="nameMaxLength"
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
          :maxlength="descriptionMaxLength"
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
      :max-length="100"
      validation="localeRequired|localeMaxLength:100"
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

import { CreateTenantMetadataRequestSchema } from '~/sdk/client/schemas.gen'

type EditableTenant = TenantResponse | UpdateTenantMetadataRequest

const { t } = useI18n()

const nameMaxLength = schemaMaxLength(CreateTenantMetadataRequestSchema, 'name')
const descriptionMaxLength = schemaMaxLength(CreateTenantMetadataRequestSchema, 'description')

const props = defineProps<{
  modelValue: EditableTenant
}>()

const emit = defineEmits<{
  'update:modelValue': [EditableTenant]
}>()

const initialAccessRules = ref<string[]>([...(props.modelValue.access_rules ?? [])])
const tenant = ref<EditableTenant>(props.modelValue)

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
