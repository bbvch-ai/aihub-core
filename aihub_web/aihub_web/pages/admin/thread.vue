<template>
  <div
    class="flex h-full flex-row"
  >
    <NavigationLeft
      title="Threads"
      :nav-items-map="navItems"
    />
    <NuxtPage />
  </div>
</template>

<script setup lang="ts">
import { getUserThreads, type ThreadResponse } from '@core/sdk/client'

import type { NavItem } from '@core/types/NavItem'

const route = useRoute()

const { data: threads } = useQuery<ThreadResponse[]>({
  key: () => ['threads'],
  staleTime: 1000 * 10, // 5 minutes
  enabled: true,
  query: async () => {
    return await getUserThreads({
      composable: '$fetch',
    })
  },
})

const navItems = computed<Record<string, NavItem[]>>(() => {
  const typeMap: Record<string, NavItem[]> = {}

  // Group threads by day
  threads.value?.forEach((thread: ThreadResponse) => {
    // Parse the ISO date string
    const threadDate = new Date(thread.created_at)

    // Format date as DD.MM.YYYY
    const day = threadDate.toLocaleDateString('de-DE', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
    })

    // Initialize the day group if it doesn't exist
    if (!typeMap[day]) {
      typeMap[day] = []
    }

    // Create NavItem for this thread
    const navItem: NavItem = {
      name: thread.name,
      key: thread.id,
      path: `/admin/thread/${thread.id}/overview`,
      isActive: () => route.params.thread_id === thread.id,
    }

    // Add to the appropriate day group
    typeMap[day].push(navItem)
  })

  // Sort threads within each day group from newest to oldest
  Object.keys(typeMap).forEach((day) => {
    typeMap[day].sort((a, b) => {
      // Find the original threads to compare their dates
      const threadA = threads.value?.find(t => t.id === a.key)
      const threadB = threads.value?.find(t => t.id === b.key)

      if (threadA && threadB) {
        return new Date(threadB.created_at).getTime() - new Date(threadA.created_at).getTime()
      }
      return 0
    })
  })

  return typeMap
})
</script>

<style scoped>

</style>
