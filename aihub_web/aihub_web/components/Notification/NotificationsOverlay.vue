<template>
  <div class="relative">
    <div class="relative inline-flex cursor-pointer">
      <Button
        icon="pi pi-bell"
        v-tooltip.bottom="{ value: t('bar.show_notifications') }"
        variant="text"
        rounded
        :aria-label="t('bar.show_notifications')"
        @click="togglePanel"
      />
      <Badge
        v-if="unreadCount > 0"
        :value="unreadCount"
        size="small"
        severity="danger"
        class="absolute right-0 top-0 flex -translate-y-1 translate-x-1"
      />
    </div>

    <OverlayPanel ref="op" @hide="isPanelOpen = false">
      <DataView :value="notifications" :loading="isLoading" scrollHeight="70vh">
        <template #header>
          <div class="flex items-center justify-between">
            <span class="text-xl font-bold">{{ t('notification.title') }} ({{ unreadCount }})</span>
            <Button
              v-if="unreadCount > 0"
              :label="t('notification.mark_all_as_read')"
              severity="secondary"
              text
              size="small"
              @click="markAllAsRead"
            />
          </div>
        </template>

        <template #list="{ items }">
          <div class="flex flex-col">
            <div
              v-for="item in items"
              :key="item.id"
              class="flex cursor-pointer items-start gap-4 p-4 transition-colors duration-200 hover:bg-surface-100 dark:hover:bg-surface-800"
              :class="[
                { 'bg-primary-50 dark:bg-primary-700 font-semibold': !item.read },
                'border-b border-surface-200 dark:border-surface-800'
              ]"
              @click="handleNotificationClick(item)"
            >
              <div v-if="!item.read" class="h-2.5 w-2.5 flex-shrink-0 self-center rounded-full bg-primary-500"/>

              <div class="flex-grow">
                <p
                  class="text-sm font-bold text-surface-800 dark:text-surface-100"
                >
                  {{ item.title.en }}
                </p>
                <p
                  class="text-sm text-surface-600 dark:text-surface-400"
                >
                  {{ item.message.en }}
                </p>
                <span class="mt-1 block text-xs text-surface-400 dark:text-surface-500">{{
                    getTimeAgo(item.created_at).text
                  }}</span>
              </div>
            </div>
          </div>
        </template>

        <template #footer>
          <div class="text-center dark:border-surface-700">
            <Button
              :label="t('notification.view_all')"
              link
              @click="viewAll"
            />
          </div>
        </template>

        <template #empty>
          <div class="flex flex-col items-center justify-center p-8 text-center text-surface-500">
            <i class="pi pi-bell p-4 text-4xl text-surface-400"/>
            <p>{{ t('notification.no_unread_notifications') }}</p>
          </div>
        </template>
      </DataView>
    </OverlayPanel>
  </div>
</template>

<script setup lang="ts">
import {computed, ref} from 'vue'
import {useRouter} from 'vue-router'
import {useI18n} from 'vue-i18n'
import {type NotificationDto} from '@core/sdk/client'

const {t} = useI18n()
const op = ref()
const router = useRouter()
const localeRoute = useLocaleRoute()
const isPanelOpen = ref(false)

const readFilter = ref<boolean | undefined>(false)

const {notifications, isLoading} = useNotifications({read: readFilter})

const {mutate: updateNotification} = useUpdateNotification()
const {mutate: updateNotifications} = useUpdateMultipleNotifications()
const {getTimeAgo} = useTimeAgo()

const unreadCount = computed(() => {
  if (!notifications.value) return 0
  return notifications.value.filter(n => !n.read).length
})

const togglePanel = (event: Event) => {
  op.value.toggle(event)
  isPanelOpen.value = !isPanelOpen.value
  if (isPanelOpen.value) {
    readFilter.value = false
  }
}

const handleNotificationClick = (notification: NotificationDto) => {
  if (!notification.read) {
    updateNotification({
      id: notification.id,
      payload: {read: true},
    })
  }
  if (notification.link) {
    router.push(localeRoute(notification.link))
    op.value.hide()
  }
}

const markAllAsRead = () => {
  updateNotifications({
    payload: {read: true},
    ids: notifications.value.map(n => n.id),
  })
}

const viewAll = () => {
  op.value.hide()
  router.push(localeRoute('/notifications'))
}
</script>
