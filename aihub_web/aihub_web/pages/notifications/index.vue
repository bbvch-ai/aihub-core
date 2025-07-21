<template>
  <StructuralScreen>
    <StructuralColumn :title="t('notification.title')" :loading="isLoading">
      <DataView :value="notifications" paginator :rows="pageSize" :total-records="totalRecords" @page="onPage">
        <template #header v-if="notifications.length > 0">
          <div class="flex justify-between">
            <div>
              <Checkbox
                v-model="selectAll"
                :binary="true"
                class="flex-shrink-0"
              />
              <span>{{ t('notification.select_all') }}</span>
            </div>
            <div class="flex gap-2" v-if="selectedNotifications.length > 0">


              <Button
                :label="t('notification.mark_as_read')"
                icon="pi pi-eye"
                severity="secondary"
                size="small"
                @click="markSelectedAsRead"
              />
              <Button
                :label="t('notification.mark_as_done')"
                icon="pi pi-check"
                severity="secondary"
                size="small"
                @click="markSelectedAsDone"
              />
            </div>
          </div>
        </template>

        <template #list="{ items }">
          <div class="flex flex-col">
            <div
              v-for="item in items"
              :key="item.id"
              class="flex  items-center gap-4 p-4"
              :class="[
                {'cursor-pointer hover:bg-surface-100 dark:hover:bg-surface-800': item.link},
                { 'bg-primary-50 dark:bg-primary-700 font-semibold': !item.read && !item.done && !item.link },
                { 'opacity-50': item.done },
                { 'bg-primary-50 dark:bg-primary-900/30 font-semibold': !item.read && !item.done },
                'border-b border-surface-200 dark:border-surface-700'
              ]"
            >
              <Checkbox
                v-model="selectedNotifications"
                :value="item"
                class="flex-shrink-0"
              />

              <div class="flex-grow" v-tooltip="{ value: t('notification.click_to_view') }"
                   @click="handleNotificationClick(item)">
                <p class="text-sm font-bold text-surface-800 dark:text-surface-100"
                >
                  {{ item.title.en }}
                </p>
                <p class="text-sm text-surface-600 dark:text-surface-400">
                  {{ item.message.en }}
                </p>
                <span class="mt-1 block text-xs text-surface-400 dark:text-surface-500">{{
                    timeAgo(item.created_at)
                  }}</span>
              </div>
              <Button
                v-if="!item.read"
                icon="pi pi-eye"
                v-tooltip.bottom="{ value: t('notification.mark_as_read') }"
                variant="text"
                rounded
                :aria-label="t('notification.mark_as_read')"
                @click="markAsRead(item)"
              />
              <Button
                v-if="!item.done"
                icon="pi pi-check-square"
                v-tooltip.bottom="{ value: t('notification.mark_as_done') }"
                variant="text"
                rounded
                :aria-label="t('notification.mark_as_done')"
                @click="markAsDone(item)"
              />
            </div>
          </div>
        </template>
        <template #paginatorstart>
          <Button type="button" icon="pi pi-refresh" text @click="refetch"/>
        </template>
      </DataView>
    </StructuralColumn>
  </StructuralScreen>
</template>

<script setup lang="ts">
import {ref} from 'vue'
import {useI18n} from 'vue-i18n'
import {useRouter} from 'vue-router'
import {type NotificationDto} from '@core/sdk/client'

const {t} = useI18n()
const router = useRouter()
const localeRoute = useLocaleRoute()

const selectedNotifications = ref<NotificationDto[]>([])

const {
  notifications,
  isLoading,
  refetch,
  totalRecords,
  pageSize,
  setPage
} = usePaginatedNotifications()

const {mutate: updateNotification} = useUpdateNotification()
const {getTimeAgo} = useTimeAgo()

const timeAgo = (timestamp: string | Date) => getTimeAgo(new Date(timestamp)).text

const onPage = (event) => {
  setPage(event.page + 1)
}

const selectAll = computed({
  get() {
    if (notifications.value.length === 0) return false
    return selectedNotifications.value.length === notifications.value.length
  },
  set(value) {
    selectedNotifications.value = value ? [...notifications.value] : []
  },
})

const handleNotificationClick = (notification: NotificationDto) => {
  if (notification.link) {
    if (!notification.read) {
      updateNotification({id: notification.id, payload: {read: true}})
    }
    router.push(localeRoute(notification.link))
  }
  refetch()
}

const markSelectedAsDone = () => {
  selectedNotifications.value.forEach((notification) => {
    if (!notification.done) {
      updateNotification({id: notification.id, payload: {done: true, read: true}})
    }
  })
  selectedNotifications.value = []
}

const markSelectedAsRead = () => {
  selectedNotifications.value.forEach((notification) => {
    if (!notification.read) {
      updateNotification({id: notification.id, payload: {read: true}})
    }
  })
  selectedNotifications.value = []
}

const markAsDone = (notification: NotificationDto) => {
  if (!notification.done) {
    updateNotification({id: notification.id, payload: {done: true, read: true}})
  }
}

const markAsRead = (notification: NotificationDto) => {
  if (!notification.read) {
    updateNotification({id: notification.id, payload: {read: true}})
  }
}
</script>
