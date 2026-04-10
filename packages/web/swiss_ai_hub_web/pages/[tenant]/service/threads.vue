<template>
  <StructuralScreen>
    <StructuralColumn
      :title="t('thread.title')"
      :loading="isLoading"
    >
      <ThreadList
        :threads="threads"
        @selected="toThread"
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
import type { ThreadDto } from '@core/sdk/client'

const router = useRouter()
const tenantPath = useTenantPath()
const { t } = useI18n()

const {
  threads,
  isLoading,
  pagination,
  currentPage,
  pageSize,
  setPage,
  setPageSize,
} = useThreads()

const toThread = (thread: ThreadDto) => {
  router.push(tenantPath(`/service/threads/${thread.id}/overview`))
}

const onPageChange = (event) => {
  setPageSize(event.rows)
  const newPage = Math.floor(event.first / event.rows) + 1
  setPage(newPage)
}
</script>
