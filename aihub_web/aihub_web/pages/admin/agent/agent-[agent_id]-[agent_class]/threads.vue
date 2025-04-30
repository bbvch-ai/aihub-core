<template>
  <div>
    <ThreadList
      :threads="threads ?? []"
      @selected="toThread"
    />
  </div>
</template>

<script setup lang="ts">
import useAgentThreads from '@core/composables/useAgentThreads'

import type { ThreadDto } from '@core/sdk/client'

const router = useRouter()
const localePath = useLocalePath()

const { data: threads } = useAgentThreads()

const toThread = (thread: ThreadDto) => {
  console.log('To thread', thread)
  router.push(localePath(`/admin/thread/${thread.id}/overview`))
}
</script>

<style scoped>

</style>
