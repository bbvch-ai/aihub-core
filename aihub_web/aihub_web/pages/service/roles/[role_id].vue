<template>
  <StructuralColumn
    :title="role?.name"
    close-route="/service/roles"
    :loading="roleIsLoading"
    size="small"
  >
    <div class="flex flex-col gap-12">
      <Panel
        class="panel pt-5"
      >
        <div class="grid grid-cols-2 gap-2 xl:grid-cols-2">
          <div class="flex flex-col items-start gap-2">
            <span class="font-semibold">
              {{ t('role.name') }}
            </span>
            <Tag
              :value="role.name"
              severity="secondary"
            />
          </div>
          <div class="flex flex-col items-start gap-2">
            <span class="text-xs">
              {{ t('role.description') }}
            </span>
            <Tag
              :value="role.description"
              severity="secondary"
            />
          </div>
        </div>
      </Panel>
      <div class="flex flex-col gap-3">
        <h2 class="text-xl">
          {{ t('role.edit') }}
        </h2>
        <RoleEdit
          v-model="clonedRole"
        />
        <Button
          type="button"
          :label="t('role.save_button')"
          icon="pi pi-save"
          :disabled="!clonedRole.name || !clonedRole.description || !clonedRole.access_rules?.length "
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
  agent_calls_limit: null,
  agent_calls_period: '1mo',
})
watch(role, (newRole: RoleResponse) => {
  if (!newRole) {
    return
  }
  clonedRole.value = cloneDeep(newRole)
})

const saveRole = async () => {
  console.log({ roleId: role.value.id, updatedRole: clonedRole.value })
  await updateRole({ roleId: role.value.id, updatedRole: clonedRole.value })
  toast.add({ severity: 'success', summary: t('role.role_saved.summary'), detail: t('role.role_saved.detail'), life: 3000 })
}
</script>

<style scoped>
.panel :deep(.p-panel-header) {
  padding: 0 !important;
}
</style>
