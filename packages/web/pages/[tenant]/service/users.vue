<template>
  <StructuralScreen>
    <StructuralColumn
      :title="t('user.title')"
      :loading="usersAreLoading"
    >
      <UserList
        :users="users"
        :available-roles="roles ?? []"
        @selected="toUser"
        @assign="onAssign"
        @revoke="onRevoke"
      />

      <div class="mt-4">
        <Paginator
          :rows="pageSize"
          :total-records="pagination.total"
          :rows-per-page-options="[10, 20, 30, 50]"
          :first="(currentPage - 1) * pageSize"
          @page="onPageChange"
        />
      </div>
    </StructuralColumn>
    <NuxtPage />
  </StructuralScreen>
</template>

<script setup lang="ts">
import type { UserDto } from '@core/sdk/client'

const router = useRouter()
const tenantPath = useTenantPath()
const { t } = useI18n()
const { tenantId } = useTenant()
const toast = useToast()

const {
  users,
  usersAreLoading,
  pagination,
  currentPage,
  pageSize,
  setPage,
  setPageSize,
} = useUsers()
const { roles } = useRoles()
const { assignRole } = useAssignRoleToUser()
const { revokeRole } = useRevokeRoleFromUser()

const toUser = (user: UserDto) => {
  router.push(tenantPath(`/service/users/${user.id}`))
}

const onPageChange = (event) => {
  setPageSize(event.rows)
  const newPage = Math.floor(event.first / event.rows) + 1
  setPage(newPage)
}

const onAssign = async ({ user, roleName }: { user: UserDto, roleName: string }) => {
  try {
    await assignRole({ tenantId: tenantId.value!, userId: user.id, roleName })
    toast.add({
      severity: 'success',
      summary: t('user.role_chips.assigned_toast', { role: roleName, user: user.name }),
      life: 3000,
    })
  }
  catch (error) {
    console.error('Failed to assign role', error)
  }
}

const onRevoke = async ({ user, roleName }: { user: UserDto, roleName: string }) => {
  try {
    await revokeRole({ tenantId: tenantId.value!, userId: user.id, roleName })
    toast.add({
      severity: 'success',
      summary: t('user.role_chips.revoked_toast', { role: roleName, user: user.name }),
      life: 3000,
    })
  }
  catch (error) {
    console.error('Failed to revoke role', error)
  }
}
</script>
