<template>
  <StructuralSubstructure>
    <StructuralColumn
      :title="t('thread.display.title')"
      close-route="/service/threads"
      keep-query
      :loading="threadIsLoading"
    >
      <DisplayList
        :displays="thread.displays"
        @selected="toDisplay"
      />
    </StructuralColumn>
    <NuxtPage />
  </StructuralSubstructure>
</template>

<script setup lang="ts">
import type { DisplayStatistics } from '@core/sdk/client'

const router = useRouter()
const route = useRoute()
const tenantPath = useTenantPath()
const { t } = useI18n()

const { thread, threadIsLoading } = useThread()

const toDisplay = (display: DisplayStatistics) => {
  router.push({
    path: tenantPath(`/service/threads/${thread.value.id}/display/${display.display_id}`),
    query: route.query,
  })
}
</script>
