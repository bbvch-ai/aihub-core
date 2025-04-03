<template>
  <div
    class="flex flex-row gap-2"
  >
    <Avatar
      :label="avatarLabel"
      class="mr-2"
      size="large"
      shape="circle"
      :class="{ 'bg-surface-800 text-white dark:bg-surface-200 dark:text-black': message.role == 'user' }"
    />
    <div class="w-full">
      <div class="flex flex-row gap-2">
        <p class="text-sm font-bold">
          {{ name }}
        </p>
        <p class="text-sm">
          {{ preferredUsername }}
        </p>
      </div>
      <div
        v-for="(block, index) in message.blocks"
        :key="index"
        class="w-full rounded-lg bg-white p-3 dark:bg-surface-700"
      >
        <p v-if="block?.text">
          {{ block.text }}
        </p>
        <img
          v-if="block.image"
          :src="block.image ?? block.path ?? block.url"
        >
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { AssistantChatMessageOutput, ChatMessageOutput, UserChatMessageOutput } from '@core/sdk/client'

const props = defineProps<{
  message: ChatMessageOutput | UserChatMessageOutput | AssistantChatMessageOutput
  name: string
  preferredUsername?: string
}>()

const avatarLabel = computed(() => {
  return props.name?.at(0) || 'U'
})
</script>

<style scoped>

</style>
