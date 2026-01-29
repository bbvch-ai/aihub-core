<template>
  <StructuralColumn
    :title="role?.name"
    close-route="/service/roles"
    :loading="roleIsLoading"
    size="small"
  >
    <div class="flex flex-col gap-4">
      <RoleEdit
        v-model="clonedRole"
      />
      <div class="flex justify-end">
        <Button
          type="button"
          :label="t('role.save_button')"
          icon="pi pi-save"
          :disabled="!clonedRole.name || !clonedRole.description || !clonedRole.access_rules?.length"
          @click="saveRole"
        />
      </div>
    </div>
  </StructuralColumn>
</template>

<script setup lang="ts">
import { useUpdateRole } from '@core/composables/role/useUpdateRole'
import cloneDeep from 'lodash.clonedeep'

import type { CreateRoleRequest, RoleResponse } from '@core/sdk/client'

const { role, roleIsLoading } = useRole()
const { t } = useI18n()
const toast = useToast()

const { updateRole } = useUpdateRole()

const clonedRole = ref<CreateRoleRequest>({
  name: '',
  description: '',
  access_rules: [],
})
watch(role, (newRole: RoleResponse) => {
  if (!newRole) {
    return
  }
  clonedRole.value = cloneDeep(newRole)
})

const saveRole = async () => {
  await updateRole({ roleId: role.value.id, updatedRole: clonedRole.value })
  toast.add({ severity: 'success', summary: t('role.role_saved.summary'), detail: t('role.role_saved.detail'), life: 3000 })
}
</script>
