<template>
  <StructuralScreen>
    <StructuralColumn
      :title="t('thread.title')"
      :loading="isLoading"
    >
      <div class="mb-4 flex items-center justify-between">
        <div class="mr-2 flex items-center gap-2">
          <DatePicker
            v-model="dateRange"
            show-button-bar
            selection-mode="range"
            :manual-input="false"
            :placeholder="t('thread.list.filter.date_range_placeholder')"
            update-model-type="string"
            show-clear
            show-icon
            date-format="yy-mm-dd"
            class="w-48"
          />
          <Select
            v-model="status"
            :options="statusOptions"
            option-label="label"
            option-value="value"
            :placeholder="t('thread.list.filter.status_placeholder')"
            show-clear
            class="w-48"
          />
          <Select
            v-model="agentInstanceId"
            :options="agentInstanceOptions"
            option-label="label"
            option-value="value"
            :placeholder="t('thread.list.filter.agent_name_placeholder')"
            show-clear
            class="w-48"
          />
          <Select
            v-model="userSearchId"
            :options="userOptions"
            option-label="label"
            option-value="value"
            :placeholder="t('thread.list.filter.user_name_placeholder')"
            show-clear
            class="w-48"
          />
        </div>
        <InputText
          v-model="searchQuery"
          :placeholder="t('thread.list.search_placeholder')"
        />
      </div>
      <ThreadList
        :threads="threads"
        :sort-field="sortField"
        :sort-order="sortOrder"
        @selected="toThread"
        @sort="onSort"
      />

      <div class="mt-4">
        <Paginator
          :rows="pageSize"
          :total-records="pagination.total"
          :rows-per-page-options="[10, 20, 30, 50]"
          :first="(currentPage - 1) * pageSize"
          template="FirstPageLink PrevPageLink CurrentPageReport NextPageLink LastPageLink RowsPerPageDropdown"
          current-page-report-template="Showing {first} to {last} of {totalRecords}"
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
  sortField,
  sortOrder,
  setSort,
  searchQuery,
  agentInstanceId,
  userSearchId,
  status,
  dateRange,
} = useThreads()

const { agentInstances } = useAgentInstances()

const { users } = useUsers()

const onSort = ({ field, order }: { field: string, order: 1 | -1 }) =>
  setSort(field as ThreadSortField, order)

const toThread = (thread: ThreadDto) => {
  router.push(tenantPath(`/service/threads/${thread.id}/overview`))
}

const onPageChange = (event) => {
  setPageSize(event.rows)
  const newPage = Math.floor(event.first / event.rows) + 1
  setPage(newPage)
}

const agentInstanceOptions = computed(() => {
  if (!agentInstances.value) return []

  return agentInstances.value.map(agentInstance => ({
    label: agentInstance.agent_config.name,
    value: agentInstance.agent_config.agent_id,
  }))
},
)

const userOptions = computed(() => {
  if (!users.value) return []

  return users.value.map(user => ({
    label: user.name,
    value: user.id,
  }))
},
)

const statusOptions = computed(() => [
  { label: t('thread.list.filter.active'), value: 'active' },
  { label: t('thread.list.filter.completed'), value: 'completed' },
  { label: t('thread.list.filter.failed'), value: 'failed' },
])
</script>
