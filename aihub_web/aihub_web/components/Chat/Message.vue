<template>
  <div
    class="flex w-full"
    :class="justifyClass"
  >
    <div
      class="flex max-w-[80%] gap-2"
      :class="flowClass"
    >
      <Avatar
        size="large"
        :shape="message.role == 'user' ? 'circle' : 'square'"
        class="shrink-0"
        :image="image"
        :class="{ 'bg-surface-800 text-white dark:bg-surface-200 dark:text-black': message.role == 'user' }"
      >
        <Icon
          v-if="icon"
          :name="message.role == 'user' ? 'lucide:user-round' : icon"
          size="xl"
        />
      </Avatar>
      <div class="flex w-full flex-col">
        <div
          class="mb-1 line-clamp-1 flex items-center gap-2 text-black dark:text-white"
          :class="justifyClass"
        >
          <p class="text-sm font-bold">
            {{ name }}
          </p>
          <p class="text-xs">
            {{ preferredUsername }}
          </p>
        </div>
        <div
          v-for="(block, index) in message.blocks"
          :key="index"
          class="mb-1 w-full max-w-[90%] rounded-3xl bg-surface-50 px-5  py-2 dark:bg-surface-800 "
          :class="{ 'cursor-pointer': isClickable, 'hover:opacity-80': isClickable }"
        >
          <p v-if="block?.block_type === 'text'">
            {{ block.text }}
          </p>
          <img
            v-if="block?.block_type === 'image'"
            :src="block.url"
          >
        </div>
        <span
          v-if="props.date"
          class="ml-0.5 flex w-full translate-y-px text-xs font-medium text-surface-400"
        >
          {{ useDateFormat(props.date, 'DD.MM.YYYY HH:mm:ss') }}
        </span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

import type { AssistantChatMessageOutput, ChatMessageOutput, UserChatMessageOutput } from '@core/sdk/client'

const props = defineProps<{
  message: ChatMessageOutput | UserChatMessageOutput | AssistantChatMessageOutput
  name: string
  preferredUsername?: string
  date?: Date
  image?: string
  icon?: string
  isClickable?: boolean
}>()

const justifyClass = computed<string[]>(() => {
  return [props.message.role === 'user' ? 'justify-end' : 'justify-start']
})
const flowClass = computed<string[]>(() => {
  return [props.message.role === 'user' ? 'flex-row-reverse' : 'flex-row']
})
</script>
