<template>
  <div class="relative inline-flex cursor-pointer">
    <Button
      v-tooltip.bottom="{ value: t('bar.show_notifications') }"
      icon="pi pi-bell"
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

  <Popover
    ref="op"
    class="[--p-popover-background:#f9f9f9] [--p-popover-border-color:#e3e3e3] dark:[--p-popover-background:#0d0d0d] dark:[--p-popover-border-color:#333]"
    @hide="isPanelOpen = false"
  >
    <ScrollPanel>
      <DataView
        :value="unreadNotifications"
        :loading="isLoading"
        :style="{
          '--p-dataview-content-background': 'transparent',
          '--p-dataview-header-background': 'transparent',
          '--p-dataview-footer-background': 'transparent',
        }"
      >
        <template #header>
          <div class="flex items-center justify-between">
            <h2 class="text-xl">
              {{ t('notification.title') }} ({{ unreadCount }})
            </h2>
            <Button
              v-if="unreadCount > 0"
              :label="t('notification.mark_all_as_read')"
              severity="secondary"
              variant="text"
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

        <template #empty>
          <div class="flex flex-col items-center justify-center p-8 text-center">
            <i class="pi pi-bell-slash p-4 text-2xl text-surface-400" />
            <p class="text-sm text-surface-500 dark:text-surface-400">
              {{ t('notification.no_unread_notifications') }}
            </p>
          </div>
        </template>

        <template #footer>
          <div class="text-center dark:border-surface-700">
            <Button
              :label="t('notification.view_all')"
              class="w-full"
              variant="text"
              @click="viewAll"
            />
          </div>
        </template>
      </DataView>
    </ScrollPanel>
  </Popover>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

import type { NotificationDto } from '@core/sdk/client'

const { t } = useI18n()
const op = ref()
const router = useRouter()
const tenantPath = useTenantPath()
const isPanelOpen = ref(false)

const readFilter = ref<boolean | undefined>(false)
const currentPage = ref(1)
const pageSize = ref(15)
const listMinHeight = ref('auto')

const { notifications, isLoading, refetch } = useNotifications({
  currentPage,
  pageSize,
  filters: { read: readFilter },
})

const { mutate: updateNotification } = useUpdateNotification()
const { mutate: updateMultipleNotifications } = useUpdateMultipleNotifications()
const { tenantId } = useTenant()

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
    updateNotification({ id: notification.id, payload: ref({ read: true }), tenantId: tenantId.value! })
  }
  if (notification.link) {
    router.push(tenantPath(notification.link))
    op.value.hide()
  }
}

const markAllAsRead = () => {
  const unreadIds = unreadNotifications.value.map(n => n.id)
  if (unreadIds.length > 0) {
    updateMultipleNotifications({
      ids: unreadIds,
      payload: ref({ read: true }),
      tenantId: tenantId.value!,
    })
    op.value.hide()
  }
}

const viewAll = () => {
  op.value.hide()
  router.push(tenantPath('/notifications'))
}
</script>
