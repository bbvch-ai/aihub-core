<template>
  <div>
    <span class="mb-8 block text-surface-500 dark:text-surface-400">
      {{ t('role.create_dialog.description') }}
    </span>
    <div class="mb-4 flex flex-col gap-4">
      <RoleEdit
        v-model="role"
      />
      <div class="flex justify-end gap-2">
        <Button
          type="button"
          :label="t('evaluation.dataset.cancel')"
          severity="secondary"
          @click="close"
        />
        <Button
          type="button"
          :label="t('evaluation.dataset.save')"
          :disabled="!role.name || !role.description || !role.access_rules?.length"
          @click="save"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'

import type { CreateRoleRequest } from '@core/sdk/client'

const { t } = useI18n()

const role = ref<CreateRoleRequest>({
  name: '',
  description: '',
  access_rules: [],
})

const emit = defineEmits<{
  close: []
}>()

const { tenantId } = useTenant()
const { createRole } = useCreateRole()

const close = () => {
  emit('close')
}
const save = async () => {
  await createRole({ createdRole: role.value, tenantId: tenantId.value! })
  emit('close')
}
</script>

<style scoped>

</style>
