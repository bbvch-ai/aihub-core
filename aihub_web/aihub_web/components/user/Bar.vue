<template>
  <div
    v-if="userStore.user"
    class="flex items-center gap-5 pr-5"
  >
    <div>
      <p class="text-xs font-bold">
        {{ userName }}
      </p>
      <p class="text-xs">
        {{ userEmail }}
      </p>
    </div>
    <OverlayBadge
      value="4"
      severity="danger"
      class="inline-flex"
      size="small"
    >
      <Avatar
        :image="userStore.user.profile_image"
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
const userEmail = computed(() => {
  return userStore.user?.email
})

const userInitials = computed(() => {
  return userStore.user?.name?.split(' ').map(n => n[0]).join('')
})
</script>

<style scoped>

</style>
