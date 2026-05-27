<!-- SPDX-License-Identifier: LicenseRef-Proprietary -->
<template>
  <StructuralColumn
    :title="t('user.title')"
    :loading="usersAreLoading"
    size="normal"
  >
    <UserList :users="users" />
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
</template>

<script setup lang="ts">
definePageMeta({ layout: 'sysadmin' })

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

const onPageChange = (event: { first: number, rows: number }) => {
  setPageSize(event.rows)
  const newPage = Math.floor(event.first / event.rows) + 1
  setPage(newPage)
}
</script>
