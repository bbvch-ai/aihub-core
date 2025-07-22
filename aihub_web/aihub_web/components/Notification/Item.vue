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
      @change="$emit('toggle-selection', notification)"
      class="flex-shrink-0 mt-1"
    />
    <div v-if="!notification.read" class="h-2.5 w-2.5 flex-shrink-0 self-center rounded-full bg-primary-500"/>
    <div class="flex-grow min-w-0">
      <div class="flex items-start justify-between gap-2">
        <div
          class="min-w-0 flex-grow rounded focus:outline-none focus:ring-2 focus:ring-primary-500 cursor-pointer"
          @click="$emit('click', notification)"
          @keydown.enter="$emit('click', notification)"
          @keydown.space.prevent="$emit('click', notification)"
          :tabindex="0"
          role="link"
        >
          <p class="text-sm font-bold text-surface-800 dark:text-surface-100 truncate flex items-center gap-2">
            <i :class="notificationIcon" class="text-base"/>
            <span>{{ notification.title.en }}</span>
          </p>
          <p class="text-sm text-surface-600 dark:text-surface-400 mt-1 line-clamp-2">
            {{ notification.message.en }}
          </p>
          <div class="flex items-center gap-2 mt-2 flex-wrap">
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
          @click.stop="$emit('click', notification)"
          class="flex-shrink-0 self-start"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import {computed} from 'vue'
import {useI18n} from 'vue-i18n'
import {useTimeAgo} from '@core/composables/useTimeAgo'
import type {NotificationDto} from '@core/sdk/client'

const props = defineProps<{
  notification: NotificationDto,
  isSelected: boolean,
  showCheckbox?: boolean
}>()

defineEmits<{
  (e: 'click', notification: NotificationDto): void
  (e: 'toggle-selection', notification: NotificationDto): void
}>()


const {t} = useI18n()
const {getTimeAgo} = useTimeAgo()

const timeAgoText = computed(() => getTimeAgo(new Date(props.notification.created_at)).text)

const notificationClasses = computed(() => [
  'border-b border-surface-200 dark:border-surface-700 cursor-pointer hover:bg-surface-50 dark:hover:bg-surface-800',
  {
    'bg-primary-100 dark:bg-primary-800': !props.notification.read && !props.notification.done,
    'opacity-60': props.notification.done,
  }
])

const severityBadgeColor = computed(() => {
  switch (props.notification.severity) {
    case 'critical':
      return 'danger'
    case 'high':
      return 'warn'
    case 'medium':
      return 'info'
    default:
    case 'low':
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
