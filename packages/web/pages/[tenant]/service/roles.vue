<template>
  <StructuralScreen>
    <StructuralColumn
      :title="t('role.title')"
      :loading="rolesAreLoading"
    >
      <div class="grid grid-cols-2 gap-4 2xl:grid-cols-2">
        <RoleCard
          v-for="role in roles"
          :key="role.id"
          :role="role"
          @click="() => toRole(role)"
          @delete="confirmDeleteRole"
        />
        <div
          class="flex min-h-full cursor-pointer flex-col justify-center gap-3 rounded-xl border-2 border-dashed border-surface-300 p-4 hover:border-primary-500 hover:bg-surface-50 dark:border-surface-600 dark:hover:bg-surface-800"
          @click="createModalOpen = true"
        >
          <div class="flex items-center justify-center">
            <div class="flex items-center justify-center p-3">
              <i
                class="pi pi-plus text-surface-400"
                style="font-size: 1.5rem"
              />
            </div>
          </div>
          <div class="text-center">
            <h3 class="font-medium text-surface-600 dark:text-surface-400">
              {{ t('role.create_new') }}
            </h3>
          </div>
        </div>
        <Dialog
          v-model:visible="createModalOpen"
          modal
          :header="t('role.create_new')"
        >
          <RoleCreate
            @close="createModalOpen = false"
          />
        </Dialog>
      </div>
    </StructuralColumn>
    <NuxtPage />
  </StructuralScreen>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'

import type { RoleResponse } from '@core/sdk/client'

const router = useRouter()
const tenantPath = useTenantPath()
const { t } = useI18n()
const confirm = useConfirm()
const toast = useToast()

const { tenantId } = useTenant()
const { roles, rolesAreLoading } = useRoles()
const { deleteRole } = useDeleteRole()

const createModalOpen = ref(false)

const toRole = (role: RoleResponse) => {
  router.push(tenantPath(`/service/roles/${role.id}`))
}

const confirmDeleteRole = (role: RoleResponse) => {
  confirm.require({
    message: t('role.remove_dialog.explanation'),
    header: t('role.remove_dialog.confirm'),
    icon: 'pi pi-exclamation-triangle',
    position: 'bottom',
    rejectProps: { label: t('role.remove_dialog.cancel'), severity: 'secondary', outlined: true },
    acceptProps: { label: t('role.remove_dialog.proceed'), severity: 'danger' },
    accept: async () => {
      await router.push(tenantPath('/service/roles'))
      await deleteRole({ roleId: role.id, tenantId: tenantId.value! })
      toast.add({ severity: 'success', summary: t('role.role_deleted.summary'), detail: t('role.role_deleted.detail'), life: 3000 })
    },
  })
}
</script>
