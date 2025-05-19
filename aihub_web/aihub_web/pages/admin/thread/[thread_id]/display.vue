<template>
  <StructuralSubstructure>
    <StructuralColumn
      title="Displays"
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

const { thread, threadIsLoading } = useThread()

const toDisplay = (display: DisplayStatistics) => {
  router.push(localePath(`/admin/thread/${thread.value.id}/display/${display.display_id}`))
}
</script>
