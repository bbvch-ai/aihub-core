<template>
  <ProgressBar
    v-if="isLoading || !threads"
    mode="indeterminate"
    style="height: 2px"
  />
  <div class="card p-3">
    <div class="mb-4">
      <h2 class="text-xl font-bold">
        Agent Threads
      </h2>
    </div>

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
  </div>
</template>

<script setup lang="ts">
import type { ThreadDto } from '@core/sdk/client'

import { useLocalePath } from '#i18n'

const router = useRouter()
const localePath = useLocalePath()

const {
  threads,
  isLoading,
  pagination,
  currentPage,
  pageSize,
  setPage,
  setPageSize,
} = useAgentThreads()

const toThread = (thread: ThreadDto) => {
  router.push(localePath(`/admin/thread/${thread.id}/overview`))
}

const onPageChange = (event) => {
  setPageSize(event.rows)
  const newPage = Math.floor(event.first / event.rows) + 1
  setPage(newPage)
}
</script>
