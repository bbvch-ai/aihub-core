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

      <AccessRulesEditor
        v-model:rules="accessRules"
        :initial-rules="[]"
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
const { createTenantMetadata } = useCreateTenantMetadata()

const tenant = ref<CreateTenantMetadataRequest>({
  tenant_id: '',
  name: '',
  description: '',
  access_rules: [],
})

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
