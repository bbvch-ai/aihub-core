<template>
  <div class="w-full">
    <div class="flex gap-2 p-1">
      <Button
        v-for="navItem in navItems"
        :key="navItem.key"
        :label="navItem.name"
        :variant="navItem.isActive() ? undefined : 'text'"
        size="small"
        severity="secondary"
        @click="toNavItem(navItem)"
      />
    </div>
    <Divider class="my-0" />
  </div>
</template>

<script setup lang="ts">
import type { NavItem } from '@core/types/NavItem'

import { useLocalePath } from '#i18n'

defineProps<{
  navItems: NavItem[]
}>()

const router = useRouter()
const localePath = useLocalePath()

const toNavItem = (navItem: NavItem) => {
  router.push(localePath(navItem.path))
}
</script>
