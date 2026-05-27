<template>
  <StructuralSubstructure>
    <StructuralColumn
      :title="t('process.title')"
      :loading="isLoading"
    >
      <ProcessWalkthroughList
        :walkthroughs="walkthroughs"
        @selected="toWalkthrough"
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
  </StructuralSubstructure>
</template>

<script setup lang="ts">
import { useProcessWalkthroughs } from '@core/composables/process/useProcessWalkthroughs'

import type { ProcessWalkthroughDto } from '@core/sdk/client'

const router = useRouter()
const tenantPath = useTenantPath()
const { t } = useI18n()

const {
  walkthroughs,
  isLoading,
  pagination,
  currentPage,
  pageSize,
  setPage,
  setPageSize,
} = useProcessWalkthroughs()

const toWalkthrough = (walkthrough: ProcessWalkthroughDto) => {
  router.push(tenantPath(`/service/processes/${walkthrough.process_class}-${walkthrough.process_id}/walkthroughs/${walkthrough.process_walkthrough_id}/overview`))
}

const onPageChange = (event) => {
  setPageSize(event.rows)
  const newPage = Math.floor(event.first / event.rows) + 1
  setPage(newPage)
}
</script>
