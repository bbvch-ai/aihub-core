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
      <ScrollPanel :style="{ minHeight: listMinHeight, maxHeight: '70vh' }">
        <DataView :value="unreadNotifications" :loading="isLoading">
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
              <NotificationItem
                v-for="item in items"
                :key="item.id"
                :notification="item"
                @click="handleNotificationClick"
              />
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
      </ScrollPanel>
    </OverlayPanel>
  </div>
</template>

<script setup lang="ts">
import {computed, ref, watch} from 'vue'
import {useRouter} from 'vue-router'
import {useI18n} from 'vue-i18n'
import type {NotificationDto} from '@core/sdk/client'

const {t} = useI18n()
const op = ref()
const router = useRouter()
const localeRoute = useLocaleRoute()
const isPanelOpen = ref(false)

const readFilter = ref<boolean | undefined>(false)
const currentPage = ref(1)
const pageSize = ref(15)
const listMinHeight = ref('auto')

const {notifications, isLoading, refetch} = useNotifications({
  currentPage,
  pageSize,
  filters: {read: readFilter},
})

const {mutate: updateNotification} = useUpdateNotification()
const {mutate: updateMultipleNotifications} = useUpdateMultipleNotifications()

const unreadNotifications = computed(() => {
  if (!notifications.value) return []
  return notifications.value.filter(n => !n.read)
})

const unreadCount = computed(() => unreadNotifications.value.length)

watch(notifications, (newVal) => {
  if (newVal.length > 0 && listMinHeight.value === 'auto') {
    const calculatedHeight = Math.min(newVal.length * 80, 400)
    listMinHeight.value = `${calculatedHeight}px`
  }
})

const togglePanel = (event: Event) => {
  op.value.toggle(event)
  isPanelOpen.value = !isPanelOpen.value
  if (isPanelOpen.value) {
    listMinHeight.value = 'auto'
    readFilter.value = false
    refetch()
  }
}

const handleNotificationClick = (notification: NotificationDto) => {
  if (!notification.read) {
    updateNotification({id: notification.id, payload: {read: true}})
  }
  if (notification.link) {
    router.push(localeRoute(notification.link))
    op.value.hide()
  }
}

const markAllAsRead = () => {
  const unreadIds = unreadNotifications.value.map(n => n.id)
  if (unreadIds.length > 0) {
    updateMultipleNotifications({
      ids: unreadIds,
      payload: {read: true},
    })
  }
}

const viewAll = () => {
  op.value.hide()
  router.push(localeRoute('/notifications'))
}
</script>
