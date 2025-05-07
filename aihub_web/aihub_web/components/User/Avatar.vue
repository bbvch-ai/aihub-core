<template>
  <div class="flex gap-2">
    <Avatar
      :image="user.profile_image"
      size="large"
      shape="circle"
    />
    <div
      class="mb-1 flex flex-col justify-center"
    >
      <p class="text-sm font-bold">
        {{ user.name }}
      </p>
      <p class="text-sm">
        {{ user.email }}
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { UserDto } from '@core/sdk/client'

defineProps<{
  user: UserDto
}>()
</script>

<style scoped>

</style>
