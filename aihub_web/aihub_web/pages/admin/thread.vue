<template>
  <div class="flex h-full flex-row">
    <NavigationLeft
      title="Threads"
      :nav-items-map="navItems"
      :has-more="hasMoreThreads"
      :loading="threadsAreLoading"
      @load-more="loadMore"
    />
    <NuxtPage />
  </div>
</template>

<script setup lang="ts">
import type { ThreadDto } from '@core/sdk/client'
import type { NavItem } from '@core/types/NavItem'

const route = useRoute()

const {
  threads,
  threadsAreLoading,
  hasMoreThreads,
  loadMoreThreads,
} = useThreads()

const loadMore = () => {
  if (hasMoreThreads.value && !threadsAreLoading.value) {
    loadMoreThreads()
  }
}

const navItems = computed<Record<string, NavItem[]>>(() => {
  const typeMap: Record<string, NavItem[]> = {}

  // Group threads by day
  threads.value?.forEach((thread: ThreadDto) => {
    // Parse the ISO date string
    const threadDate = new Date(thread.created_at)

    // Format date as DD.MM.YYYY
    const day = threadDate.toLocaleDateString('de-CH', {
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

  // Sort day groups by date (newest first)
  const sortedKeys = Object.keys(typeMap).sort((a, b) => {
    const [dayA, monthA, yearA] = a.split('.')
    const [dayB, monthB, yearB] = b.split('.')

    const dateA = new Date(+yearA, +monthA - 1, +dayA)
    const dateB = new Date(+yearB, +monthB - 1, +dayB)

    return dateB.getTime() - dateA.getTime()
  })

  // Create a new sorted map
  const sortedMap: Record<string, NavItem[]> = {}
  sortedKeys.forEach((key) => {
    sortedMap[key] = typeMap[key]

    // Sort threads within each day group from newest to oldest
    sortedMap[key].sort((a, b) => {
      const threadA = threads.value?.find(t => t.id === a.key)
      const threadB = threads.value?.find(t => t.id === b.key)

      if (threadA && threadB) {
        return new Date(threadB.created_at).getTime() - new Date(threadA.created_at).getTime()
      }
      return 0
    })
  })

  return sortedMap
})
</script>
