<template>
  <div class="relative">
    <OverlayBadge
      :value="notifications.length"
      size="small"
    >
      <Button
        icon="pi pi-bell"
        text
        rounded
        aria-label="Notifications"
        @click="togglePanel"
      />
    </OverlayBadge>

    <OverlayPanel ref="op" :pt="{ content: { class: 'p-0' } }" @hide="isPanelOpen = false">
      <DataView :value="notifications" :loading="isLoading" scrollHeight="70vh">

        <template #header>
          <span class="text-xl font-bold">{{ t('notification.title') }}</span>
        </template>

        <template #list="{ items }">
          <div class="flex flex-col">
            <div
              v-for="item in items"
              :key="item.id"
              class="flex cursor-pointer items-start gap-4 p-4 transition-colors duration-200 hover:bg-surface-100 dark:hover:bg-surface-800"
              :class="[
              { 'bg-primary-50 dark:bg-primary-900/30 font-semibold': !item.read },
              'border-b border-surface-200 dark:border-surface-700'
            ]"
              @click="handleNotificationClick(item)"
            >
              <div class="flex-grow">
                <p class="text-sm font-bold text-surface-800 dark:text-surface-100">{{ item.title.en }}</p>
                <p class="text-sm text-surface-600 dark:text-surface-400">{{ item.message.en }}</p>
                <span class="mt-1 block text-xs text-surface-400 dark:text-surface-500">{{
                    getTimeAgo(item.created_at).text
                  }}</span>
              </div>

              <div v-if="!item.read" class="h-2.5 w-2.5 flex-shrink-0 self-center rounded-full bg-primary-500"/>
            </div>
          </div>
        </template>

        <template #empty>
          <div class="flex flex-col items-center justify-center p-8 text-center text-surface-500">
            <i class="pi pi-bell p-4 text-4xl text-surface-400"/>
            <p>{{ t('notification.no_notifications') }}</p>
          </div>
        </template>
      </DataView>
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

const {notifications, isLoading, refetch: fetchNotifications} = useNotifications()

const {mutate: updateNotification} = useUpdateNotification()
const {getTimeAgo} = useTimeAgo()


const notificationIcon = (type: NotificationDto['type']) => {
  switch (type) {
    case 'success':
      return 'mdi-check-circle'
    case 'warning':
      return 'mdi-check-circle'
    case 'danger':
      return 'mdi-check-circle'
    case 'info':
    default:
      return 'mdi-check-circle'
  }
}

const togglePanel = (event: Event) => {
  op.value.toggle(event)
  isPanelOpen.value = !isPanelOpen.value
  if (isPanelOpen.value) {
    fetchNotifications()
  }
}


const handleNotificationClick = (notification: NotificationDto) => {
  console.log('Notification clicked:', notification)
  if (!notification.read) {
    updateNotification({
      id: notification.id,
      payload: ref({read: true})
    })
  }
}
</script>
