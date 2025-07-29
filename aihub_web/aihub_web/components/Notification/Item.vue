<template>
  <div
    class="flex items-start gap-4 p-4 transition-colors duration-200"
    :class="notificationClasses"
    role="listitem"
  >
    <Checkbox
      v-if="showCheckbox"
      :model-value="isSelected"
      :binary="true"
      class="mt-1 shrink-0"
      @change="$emit('toggle-selection', notification)"
    />
    <div
      v-if="!notification.read"
      class="size-2.5 shrink-0 self-center rounded-full bg-primary-500"
    />
    <div class="min-w-0 grow">
      <div class="flex items-start justify-between gap-2">
        <div
          class="min-w-0 grow cursor-pointer rounded focus:outline-none focus:ring-2 focus:ring-primary-500"
          :tabindex="0"
          role="link"
          @click="$emit('click', notification)"
          @keydown.enter="$emit('click', notification)"
          @keydown.space.prevent="$emit('click', notification)"
        >
          <p class="flex items-center gap-2 truncate text-sm font-bold text-surface-800 dark:text-surface-100">
            <i
              :class="notificationIcon"
              class="text-base"
            />
            <span>{{ notification.title.en }}</span>
          </p>
          <p class="mt-1 line-clamp-2 text-sm text-surface-600 dark:text-surface-400">
            {{ notification.message.en }}
          </p>
          <div class="mt-2 flex flex-wrap items-center gap-2">
            <span class="text-xs text-surface-400 dark:text-surface-500">
              {{ timeAgoText }}
            </span>
            <div class="flex items-center gap-1">
              <Badge
                :value="t(`notification.severities.${notification.severity}`)"
                :severity="severityBadgeColor"
                size="small"
              />
            </div>
          </div>
        </div>

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
  </div>
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

const notificationClasses = computed(() => [
  'border-b border-surface-200 dark:border-surface-700 cursor-pointer hover:bg-surface-50 dark:hover:bg-surface-800',
  {
    'bg-primary-100 dark:bg-primary-800': !props.notification.read && !props.notification.done,
    'opacity-60': props.notification.done,
  },
])

const severityBadgeColor = computed(() => {
  switch (props.notification.severity) {
    case 'critical':
      return 'danger'
    case 'high':
      return 'warn'
    case 'medium':
      return 'info'
    case 'low':
    default:
      return 'contrast'
  }
})

const notificationIcon = computed(() => {
  switch (props.notification.type) {
    case 'success':
      return 'pi pi-check-circle'
    case 'warn':
      return 'pi pi-exclamation-triangle'
    case 'error':
      return 'pi pi-times-circle'
    case 'info':
    default:
      return 'pi pi-info-circle'
  }
})
</script>
