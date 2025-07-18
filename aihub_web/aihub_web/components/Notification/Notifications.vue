<template>
  <div class="relative">
    <OverlayBadge
      :value="unreadCount"
      severity="danger"
      size="small"
      :pt="{ badge: 'translate-x-1 translate-y-1' }"
    >
      <Button
        icon="pi pi-bell"
        text
        rounded
        aria-label="Notifications"
        @click="togglePanel"
      />
    </OverlayBadge>

    <OverlayPanel
      ref="op"
      class="w-96 p-0 shadow-lg"
      :pt="{ content: 'p-0' }"
      @hide="isPanelOpen = false"
    >
      <div class="flex flex-col bg-white dark:bg-surface-900">
        <div class="flex items-center justify-between border-b border-surface-200 p-4 dark:border-surface-700">
          <h3 class="text-xl font-bold">
            {{ t('notification.list.title') }} ({{ unreadCount }})
          </h3>
        </div>

        <div v-if="isLoading && notifications.length === 0" class="p-4">
          <div v-for="i in 3" :key="i" class="mb-3 flex items-start gap-4">
            <Skeleton shape="circle" size="2rem"/>
            <div class="flex-grow">
              <Skeleton width="70%" height="0.8rem" class="mb-2"/>
              <Skeleton width="90%" height="0.8rem"/>
            </div>
          </div>
        </div>

        <div v-else-if="!notifications || notifications.length === 0" class="p-4 text-center text-surface-500">
          {{ t('notification.list.noNotifications') }}
        </div>

        <ScrollPanel v-else ref="scrollPanelRef" class="max-h-[calc(70vh-8rem)]">
          <div class="flex flex-col">
            <div
              v-for="notification in notifications"
              :key="notification.id"
              class="flex cursor-pointer items-start gap-4 p-4 text-surface-700 hover:bg-surface-100 dark:text-surface-300 dark:hover:bg-surface-800"
              :class="{ 'bg-highlight-background text-highlight-color': !notification.read }"
              @click="handleNotificationClick(notification)"
            >
              <Tag
                :severity="notification.type"
                :icon="notificationIcon(notification.type)"
                class="flex-shrink-0"
                rounded
              />
              <div class="flex-grow">
                <p
                  class="text-sm"
                  :class="{
                    'font-bold text-surface-900 dark:text-white': !notification.read,
                    'font-semibold text-surface-600 dark:text-surface-400': notification.read,
                  }"
                >
                  {{ notification.title.en }} </p>
                <p
                  class="text-sm"
                  :class="{ 'font-semibold': !notification.read, 'font-normal': notification.read }"
                >
                  {{ notification.message.en }} </p>
                <span class="mt-1 block text-xs text-surface-400">
                  {{ timeAgo(notification.created_at).text }}
                </span>
              </div>
            </div>
            <div v-if="isLoading && notifications.length > 0" class="flex justify-center p-2">
              <i class="pi pi-spin pi-spinner"/>
            </div>
          </div>
        </ScrollPanel>
      </div>
    </OverlayPanel>
  </div>
</template>

<script setup lang="ts">
import {ref} from 'vue'
import {useI18n} from 'vue-i18n'
import {type NotificationDto} from '@core/sdk/client'

const {t} = useI18n()
const op = ref()
const isPanelOpen = ref(false)
const scrollPanelRef = ref<HTMLElement | null>(null)
const queryCache = useQueryCache()

const {notifications, isLoading, unreadCount, hasMore, loadMore} = useNotificationsInfinite()
const {getTimeAgo} = useTimeAgo()

useInfiniteScroll(
  scrollPanelRef,
  () => {
    if (hasMore.value && !isLoading.value) {
      loadMore()
    }
  },
  {distance: 10},
)

const timeAgo = (timestamp: string) => getTimeAgo(new Date(timestamp))

const notificationIcon = (type: NotificationDto['type']) => {
  switch (type) {
    case 'success':
      return 'pi pi-check-circle'
    case 'warning':
      return 'pi pi-exclamation-triangle'
    case 'danger':
      return 'pi pi-times-circle'
    case 'info':
    default:
      return 'pi pi-info-circle'
  }
}

const togglePanel = (event: Event) => {
  op.value.toggle(event)
  isPanelOpen.value = !isPanelOpen.value
  if (isPanelOpen.value) {
    queryCache.invalidateQueries({queryKey: ['notifications_infinite']})
  }
}

const {mutate: updateNotification} = useUpdateNotification()

const handleNotificationClick = (notification: NotificationDto) => {
  if (!notification.read) {
    updateNotification({
      id: notification.id,
      payload: {read: true}
    })
  }
}
</script>
