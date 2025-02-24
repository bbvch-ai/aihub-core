<template>
  <div class="flex flex-row gap-5">
    <Button
      :icon="isDark ? 'pi pi-sun' : 'pi pi-moon'"
      variant="text"
      rounded
      aria-label="Filter"
      @click="toggleDarkMode()"
    />
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
          :label="!userStore.user.profile_image ? userInitials : undefined"
          shape="circle"
          size="normal"
        />
      </OverlayBadge>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useDark } from '@vueuse/core'
import { computed } from 'vue'
import { useUserStore } from '@core/stores/userStore'

const userStore = useUserStore()

const userName = computed(() => userStore.user?.name)
const userEmail = computed(() => userStore.user?.email)
const userInitials = computed(() =>
  userStore.user?.name?.split(' ').map(n => n[0]).join(''),
)

// Initialize the dark mode reactive state with persistence
const isDark = useDark({ storageKey: 'dark' })

function toggleDarkMode() {
  isDark.value = !isDark.value
}
</script>

<style scoped>

</style>
