<template>
  <div v-if="thread">
    <ThreadInfo
      :thread="thread"
    />
  </div>
</template>

<script setup lang="ts">
import { getThread, type ThreadResponse } from '@core/sdk/client'

const route = useRoute()

const { data: thread } = useQuery<ThreadResponse>({
  key: () => ['thread', route.params.thread_id],
  staleTime: 1000 * 10, // 5 minutes
  enabled: true,
  query: async () => {
    return await getThread({
      composable: '$fetch',
      path: {
        thread_id: route.params.thread_id,
      },
    })
  },
})
</script>

<style scoped>

</style>
