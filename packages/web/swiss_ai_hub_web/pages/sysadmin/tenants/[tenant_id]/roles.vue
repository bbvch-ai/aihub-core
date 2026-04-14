<template>
  <StructuralColumn
    :title="t('role.title')"
    :loading="rolesAreLoading"
    size="small"
  >
    <div class="grid grid-cols-2 gap-4 2xl:grid-cols-2">
      <RoleCard
        v-for="role in roles"
        :key="role.id"
        :role="role"
        @click="openEdit(role)"
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
    </div>

    <Dialog
      v-model:visible="createModalOpen"
      modal
      :header="t('role.create_new')"
      class="w-full max-w-xl"
    >
      <RoleCreate @close="createModalOpen = false" />
    </Dialog>

    <Dialog
      v-model:visible="editModalOpen"
      modal
      :header="editDraft?.name"
      class="w-full max-w-xl"
    >
      <div
        v-if="editDraft"
        class="flex flex-col gap-4"
      >
        <RoleEdit v-model="editDraft" />
        <div class="flex justify-end gap-2">
          <Button
            type="button"
            :label="t('tenant_admin.cancel')"
            severity="secondary"
            @click="editModalOpen = false"
          />
          <Button
            type="button"
            :label="t('tenant_admin.save')"
            :disabled="!editDraft.name || !editDraft.description || !editDraft.access_rules?.length"
            @click="saveEdit"
          />
        </div>
      </div>
    </Dialog>
  </StructuralColumn>
</template>

<script setup lang="ts">
import RoleCreate from '@core/components/Role/Create.vue'
import RoleEdit from '@core/components/Role/Edit.vue'
import { cloneDeep } from 'lodash-es'

import type { RoleResponse } from '@core/sdk/client'

definePageMeta({ layout: 'sysadmin' })

const route = useRoute()
const { t } = useI18n()
const toast = useToast()
const confirm = useConfirm()

const tenantId = computed(() => route.params.tenant_id as string)

const { roles, rolesAreLoading } = useRoles()
const { updateRole } = useUpdateRole()
const { deleteRole } = useDeleteRole()

const createModalOpen = ref(false)
const editModalOpen = ref(false)
const editDraft = ref<RoleResponse | null>(null)

const openEdit = (role: RoleResponse) => {
  editDraft.value = cloneDeep(role)
  editModalOpen.value = true
}

const saveEdit = async () => {
  if (!editDraft.value) return
  await updateRole({ roleId: editDraft.value.id, updatedRole: editDraft.value, tenantId: tenantId.value })
  editModalOpen.value = false
  toast.add({ severity: 'success', summary: t('role.role_saved.summary'), detail: t('role.role_saved.detail'), life: 3000 })
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
      await deleteRole({ roleId: role.id, tenantId: tenantId.value })
      toast.add({ severity: 'success', summary: t('role.role_deleted.summary'), detail: t('role.role_deleted.detail'), life: 3000 })
    },
  })
}
</script>
