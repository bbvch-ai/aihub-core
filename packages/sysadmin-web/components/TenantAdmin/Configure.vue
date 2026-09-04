<template>
  <div>
    <span class="mb-6 block text-surface-500 dark:text-surface-400">
      {{ t('tenant_admin.configure.description') }}
    </span>

    <div class="mb-4 flex flex-col gap-4">
      <FloatLabel variant="in">
        <Select
          id="tenant_id_select"
          v-model="tenant.tenant_id"
          :options="unconfiguredTenantIds ?? []"
          :loading="unconfiguredTenantIdsAreLoading"
          class="w-full"
        />
        <label for="tenant_id_select">
          {{ t('tenant_admin.configure.tenant_id_label') }}
        </label>
      </FloatLabel>

      <p
        v-if="!unconfiguredTenantIdsAreLoading && (unconfiguredTenantIds?.length ?? 0) === 0"
        class="text-sm text-surface-500 dark:text-surface-400"
      >
        {{ t('tenant_admin.configure.empty_unconfigured') }}
      </p>

      <FloatLabel variant="in">
        <InputText
          id="configure_name"
          v-model="tenant.name"
          class="w-full"
        />
        <label for="configure_name">
          {{ t('tenant_admin.form.name') }}
        </label>
      </FloatLabel>

      <FloatLabel variant="in">
        <Textarea
          id="configure_description"
          v-model="tenant.description"
          rows="3"
          class="w-full"
        />
        <label for="configure_description">
          {{ t('tenant_admin.form.description') }}
        </label>
      </FloatLabel>

      <Message
        v-if="defaultAccessRulesError"
        severity="warn"
        variant="simple"
        size="small"
      >
        {{ t('tenant_admin.configure.default_rules_error') }}
      </Message>

      <AccessRulesEditor
        v-model:rules="accessRules"
        :initial-rules="defaultAccessRules ?? []"
        :restrict-to-tenant="false"
      />

      <div class="flex justify-end gap-2">
        <Button
          type="button"
          :label="t('tenant_admin.cancel')"
          severity="secondary"
          @click="close"
        />
        <Button
          type="button"
          :label="t('tenant_admin.save')"
          :disabled="!canSave"
          @click="save"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import AccessRulesEditor from '@core/components/Role/AccessRulesEditor.vue'

import type { CreateTenantMetadataRequest } from '~/sdk/client'

const { t } = useI18n()

const { unconfiguredTenantIds, unconfiguredTenantIdsAreLoading } = useUnconfiguredTenantIds()
const { defaultAccessRules, defaultAccessRulesError } = useDefaultTenantAccessRules()
const { createTenantMetadata } = useCreateTenantMetadata()

const tenant = ref<CreateTenantMetadataRequest>({
  tenant_id: '',
  name: '',
  description: '',
  // Left undefined, not [], so that a failed prefill omits the field and lets the backend derive the
  // default itself. Sending [] would read as "a tenant that deliberately starts with no access at all".
  access_rules: undefined,
})

// Seeded once, so the standard set is visible and editable before saving rather than applied invisibly
// by the backend. Guarded against re-firing so a refetch cannot discard edits already made in the form.
const defaultRulesSeeded = ref(false)
watch(defaultAccessRules, (rules) => {
  if (defaultRulesSeeded.value || !rules) return
  tenant.value.access_rules = [...rules]
  defaultRulesSeeded.value = true
}, { immediate: true })

const accessRules = computed({
  get: () => tenant.value.access_rules ?? [],
  set: (val) => { tenant.value.access_rules = val },
})

const canSave = computed(() => Boolean(tenant.value.tenant_id && tenant.value.name))

const emit = defineEmits<{
  close: []
}>()

const close = () => {
  emit('close')
}

const save = async () => {
  await createTenantMetadata({ data: tenant.value })
  emit('close')
}
</script>
