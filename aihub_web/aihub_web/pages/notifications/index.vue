<template>
  <StructuralScreen>
    <StructuralColumn :title="t('notification.title')" :loading="isLoading">
      <DataView
        :value="notifications"
        paginator
        :rows="pageSize"
        :total-records="totalRecords"
        :first="(currentPage - 1) * pageSize"
        @page="onPage"
        lazy
      >
        <template #header>
          <div class="flex flex-col sm:flex-row justify-between gap-4">
            <div class="flex items-center gap-2 flex-wrap">
              <Checkbox
                v-model="selectAll"
                :binary="true"
                :aria-label="t('notification.select_all')"
                :disabled="!hasNotifications"
              />
              <Button
                :label="t('notification.mark_as_read')"
                icon="pi pi-eye"
                severity="secondary"
                size="small"
                @click="markSelectedAsRead"
                :disabled="!canMarkSelectedAsRead"
              />
              <Button
                :label="t('notification.mark_as_done')"
                icon="pi pi-check"
                severity="secondary"
                size="small"
                @click="markSelectedAsDone"
                :disabled="!canMarkSelectedAsDone"
              />
              <Button
                v-if="hasSelectedNotifications"
                :label="t('notification.clear_selection')"
                icon="pi pi-times"
                severity="secondary"
                size="small"
                text
                @click="clearSelection"
              />
            </div>
            <div class="flex gap-2">
              <SelectButton
                v-model="activeFilter"
                :options="filterOptions"
                option-label="label"
                option-value="value"
                :allow-empty="false"
                :aria-label="t('notification.filter_notifications')"
              />
            </div>
          </div>
        </template>

        <template #list="{ items }">
          <div class="flex flex-col" role="list">
            <NotificationItem
              v-for="item in items"
              :key="item.id"
              :notification="item"
              :is-selected="isSelected(item)"
              :show-checkbox="true"
              @click="handleNotificationClick(item)"
              @toggle-selection="toggleSelection"
            />
          </div>
        </template>

        <template #empty>
          <div class="flex flex-col items-center justify-center p-8 text-center text-surface-500">
            <i class="pi pi-bell p-4 text-4xl text-surface-400" aria-hidden="true"/>
            <p class="text-lg font-medium mb-2">
              {{ getEmptyStateTitle() }}
            </p>
          </div>
        </template>
      </DataView>
    </StructuralColumn>
  </StructuralScreen>
</template>

<script setup lang="ts">
import {computed, nextTick, ref, watch} from 'vue'
import {useI18n} from 'vue-i18n'
import {useRouter} from 'vue-router'
import type {NotificationDto} from '@core/sdk/client'

const {t} = useI18n()
const router = useRouter()
const localeRoute = useLocaleRoute()

const selectedNotifications = ref<NotificationDto[]>([])
const currentPage = ref(1)
const pageSize = ref(8)

const readFilter = ref<boolean | undefined>(false)
const doneFilter = ref<boolean | undefined>(undefined)

const filterOptions = computed(() => [
  {label: t('notification.filter.unread'), value: 'unread'},
  {label: t('notification.filter.not_done'), value: 'not_done'},
  {label: t('notification.filter.all'), value: 'all'},
])

const activeFilter = ref('not_done')

const {
  notifications,
  isLoading,
  totalRecords,
} = useNotifications({
  currentPage,
  pageSize,
  filters: {
    read: readFilter,
    done: doneFilter,
  },
})

watch(() => activeFilter.value, (newPreset) => {
  const filterMap = {
    not_done: {read: undefined, done: false},
    all: {read: undefined, done: undefined},
    unread: {read: false, done: undefined}
  }

  const filters = filterMap[newPreset]
  readFilter.value = filters.read
  doneFilter.value = filters.done

  currentPage.value = 1
  selectedNotifications.value = []
}, {immediate: true})

const {mutate: updateNotification} = useUpdateNotification()
const {mutate: updateMultipleNotifications} = useUpdateMultipleNotifications()

const {getTimeAgo} = useTimeAgo()


const hasNotifications = computed(() => notifications.value.length > 0)

const hasSelectedNotifications = computed(() => selectedNotifications.value.length > 0)

const canMarkSelectedAsRead = computed(() =>
  hasSelectedNotifications.value &&
  selectedNotifications.value.some(n => !n.read)
)

const canMarkSelectedAsDone = computed(() =>
  hasSelectedNotifications.value &&
  selectedNotifications.value.some(n => !n.done)
)

const selectAll = computed({
  get: () => hasNotifications.value && selectedNotifications.value.length === notifications.value.length,
  set: (value: boolean) => {
    selectedNotifications.value = value ? [...notifications.value] : []
  },
})

const onPage = (event: any) => {
  currentPage.value = event.page + 1
  pageSize.value = event.rows
  selectedNotifications.value = []
}

const clearSelection = () => {
  selectedNotifications.value = []
}


const getEmptyStateTitle = () => {
  const titles = {
    all: t('notification.no_notifications'),
    not_done: t('notification.no_pending_notifications'),
    unread: t('notification.no_unread_notifications')
  }
  return titles[activeFilter.value] || titles.all
}


const handleNotificationClick = async (notification: NotificationDto) => {
  if (!notification.read) {
    await updateNotification({
      id: notification.id,
      payload: ref({read: true})
    })
  }
  if (!notification.link) return
  await nextTick()
  router.push(localeRoute(notification.link))
}

const markSelectedAsRead = async () => {
  if (!canMarkSelectedAsRead.value) return
  const idsToUpdate = selectedNotifications.value.map(n => n.id)

  updateMultipleNotifications({
    ids: idsToUpdate,
    payload: ref({read: true}),
  })
  selectedNotifications.value = []
}

const markSelectedAsDone = async () => {
  if (!canMarkSelectedAsDone.value) return
  const idsToUpdate = selectedNotifications.value.map(n => n.id)

  updateMultipleNotifications({
    ids: idsToUpdate,
    payload: ref({done: true, read: true}),
  })
  selectedNotifications.value = []

}

const isSelected = (item: NotificationDto) => {
  return selectedNotifications.value.some(selected => selected.id === item.id)
}

const toggleSelection = (item: NotificationDto) => {
  if (isSelected(item)) {
    selectedNotifications.value = selectedNotifications.value.filter(selected => selected.id !== item.id)
  } else {
    selectedNotifications.value.push(item)
  }
}
</script>
