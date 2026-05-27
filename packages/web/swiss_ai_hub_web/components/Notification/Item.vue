<template>
  <li
    class="flex cursor-pointer items-start gap-4 border-b border-surface-100 p-4 transition-colors duration-200 hover:bg-surface-50 dark:border-surface-800 dark:hover:bg-surface-800"
    :class="notification.done ? 'opacity-40' : ''"
  >
    <Checkbox
      v-if="showCheckbox"
      :model-value="isSelected"
      :binary="true"
      class="mt-1 shrink-0"
      @change="$emit('toggle-selection', notification)"
    />
    <div class="size-2.5 shrink-0 self-center">
      <div
        v-if="!notification.read"
        class="size-full rounded-full"
        :class="unreadCircleClasses"
      />
    </div>
    <div class="min-w-0 grow">
      <div class="flex items-start justify-between gap-2">
        <button
          type="button"
          class="min-w-0 grow cursor-pointer rounded text-left focus:outline-none focus:ring-2 focus:ring-primary-500"
          @click="$emit('click', notification)"
        >
          <p class="mb-1 text-xs font-light opacity-70">
            {{ timeAgoText }}
          </p>
          <h3 class="font-semibold opacity-80">
            {{ notification.title }}
          </h3>
          <p class="text-xs font-light opacity-70">
            {{ notification.message }}
          </p>
        </button>

        <Button
          :label="t('notification.view_button')"
          icon="pi pi-arrow-right"
          icon-pos="right"
          size="small"
          text
          class="shrink-0 self-start"
          @click.stop="$emit('click', notification)"
        />
      </div>
    </div>
  </li>
</template>

<script setup lang="ts">
import { useTimeAgo } from '@core/composables/useTimeAgo'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import type { NotificationDto } from '@core/sdk/client'

const props = defineProps<{
  notification: NotificationDto
  isSelected: boolean
  showCheckbox?: boolean
}>()

defineEmits<{
  'click': [notification: NotificationDto]
  'toggle-selection': [notification: NotificationDto]
}>()

const { t } = useI18n()
const { getTimeAgo } = useTimeAgo()

const timeAgoText = computed(() => getTimeAgo(new Date(props.notification.created_at)).text)

const unreadCircleClasses = computed(() => {
  switch (props.notification.severity) {
    case 'critical':
      return 'bg-red-500'
    case 'high':
      return 'bg-orange-500'
    case 'medium':
      return 'bg-blue-500'
    case 'low':
    default:
      return 'bg-surface-500'
  }
})
</script>
