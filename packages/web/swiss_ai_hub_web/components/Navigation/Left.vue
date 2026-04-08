<template>
  <div
    ref="scrollContainerRef"
    class="fixed flex h-[calc(100vh-50px)] w-[260px] flex-col gap-5 overflow-y-auto overflow-x-hidden bg-surface-50 dark:bg-surface-950"
  >
    <p class="pl-3 pt-10 text-sm font-medium text-surface-900 dark:text-white">
      {{ title }}
    </p>
    <div class="flex flex-col gap-5">
      <div
        v-for="(navItems, group) in navItemsMap"
        :key="group"
      >
        <div class="w-full pb-1.5 pl-2.5 text-xs font-medium text-surface-500 dark:text-surface-500">
          {{ group }}
        </div>
        <div class="flex flex-col gap-2 pr-2 text-surface-700 dark:text-surface-200">
          <div
            v-for="navItem in navItems"
            :key="navItem.key"
            class="flex w-full cursor-pointer justify-between text-ellipsis whitespace-nowrap rounded-lg px-[11px] py-[6px] hover:bg-surface-100 dark:hover:bg-surface-950"
            :class="{ 'bg-surface-200 dark:bg-surface-900': navItem.isActive() }"
            @click="toNavItem(navItem)"
          >
            <div class="flex w-full flex-1 self-center">
              <div
                dir="auto"
                class="h-[20px] w-full self-center overflow-hidden text-left"
              >
                {{ navItem.name }}
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Loading indicator at the bottom -->
      <div
        v-if="loading"
        class="flex justify-center py-4"
      >
        <i class="pi pi-spin pi-spinner text-primary" />
      </div>
    </div>
  </div>
  <div class="min-w-[260px]" />
</template>

<script setup lang="ts">
import { useInfiniteScroll } from '@vueuse/core'
import { ref } from 'vue'

import type { NavItem } from '@core/types/NavItem'

const props = defineProps<{
  title: string
  navItemsMap: Record<string, NavItem[]>
  hasMore?: boolean
  loading?: boolean
}>()

const emit = defineEmits<{
  loadMore: []
}>()

const router = useRouter()
const tenantPath = useTenantPath()
const scrollContainerRef = ref<HTMLElement | null>(null)

const toNavItem = (navItem: NavItem) => {
  router.push(tenantPath(navItem.path))
}

// Set up infinite scroll using vueuse
useInfiniteScroll(
  scrollContainerRef,
  () => {
    emit('loadMore')
  },
  {
    distance: 10,
    canLoadMore: () => props.hasMore ?? false,
  },
)
</script>
