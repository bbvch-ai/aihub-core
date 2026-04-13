<template>
  <div>
    <span class="mb-8 block text-surface-500 dark:text-surface-400">
      {{ t('tenant_admin.create_dialog.description') }}
    </span>
    <div class="mb-4 flex flex-col gap-4">
      <TenantAdminEdit
        v-model="tenant"
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
          :disabled="!tenant.name"
          @click="save"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { CreateTenantRequest } from '@core/sdk/client'

const { t } = useI18n()

const tenant = ref<CreateTenantRequest>({
  name: '',
  description: '',
  access_rules: [],
})

const emit = defineEmits<{
  close: []
}>()

const { createTenant } = useCreateTenant()

const close = () => {
  emit('close')
}

const save = async () => {
  await createTenant({ data: tenant.value })
  emit('close')
}
</script>
