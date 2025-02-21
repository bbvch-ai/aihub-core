<template>
  <div
    v-if="userStore.user"
    class="flex items-center gap-5 pr-5"
  >
    <p class="text-xs">
      {{ userName }}
    </p>
    <OverlayBadge
      value="4"
      severity="danger"
      class="inline-flex"
      size="small"
    >
      <Avatar
        :label="userInitials"
        shape="circle"
        size="normal"
      />
    </OverlayBadge>
  </div>
</template>

<script setup lang="ts">
import { useUserStore } from '@core/stores/userStore'

const userStore = useUserStore()

const userName = computed(() => {
  return userStore.user?.name
})

const userInitials = computed(() => {
  return userStore.user?.name?.split(' ').map(n => n[0]).join('')
})
</script>

<style scoped>

</style>
