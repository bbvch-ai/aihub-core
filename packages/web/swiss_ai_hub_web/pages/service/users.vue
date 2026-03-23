<template>
  <StructuralScreen>
    <StructuralColumn
      :title="t('user.title')"
      :loading="usersAreLoading"
    >
      <UserList
        :users="users"
        @selected="toUser"
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

import { useLocalePath } from '#i18n'

const router = useRouter()
const localePath = useLocalePath()
const { t } = useI18n()

const {
  users,
  usersAreLoading,
  pagination,
  currentPage,
  pageSize,
  setPage,
  setPageSize,
} = useUsers()

const toUser = (user: UserDto) => {
  router.push(localePath(`/service/users/${user.id}`))
}

const onPageChange = (event) => {
  setPageSize(event.rows)
  const newPage = Math.floor(event.first / event.rows) + 1
  setPage(newPage)
}
</script>
