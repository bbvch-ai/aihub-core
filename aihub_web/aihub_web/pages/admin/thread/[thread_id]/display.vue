<template>
  <StructuralSubstructure>
    <StructuralColumn
      :title="t('thread.display.title')"
      close-route="/admin/thread"
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
const localePath = useLocaleRoute()
const { t } = useI18n()

const { thread, threadIsLoading } = useThread()

const toDisplay = (display: DisplayStatistics) => {
  router.push(localePath(`/admin/thread/${thread.value.id}/display/${display.display_id}`))
}
</script>
