<template>
  <div
    v-if="thread && events"
  >
    <EventList
      :events="events"
      :thread="thread"
    />
  </div>
</template>

<script setup lang="ts">
import { getEvents, getThread, type ThreadResponse, type WsServerEvent } from '@core/sdk/client'

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

const { data: events } = useQuery<WsServerEvent[]>({
  key: () => ['events', 'thread', route.params.thread_id],
  staleTime: 1000 * 10, // 5 minutes
  enabled: true,
  query: async () => {
    return await getEvents({
      composable: '$fetch',
      query: {
        thread_id: route.params.thread_id,
      },
    })
  },
})
</script>

<style scoped>

</style>
