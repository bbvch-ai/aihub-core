<template>
  <DataTable
    :value="threads"
    lazy
    :sort-field="sortField"
    :sort-order="sortOrder"
    table-style="min-width: 50rem"
    selection-mode="single"
    :selection="selectedThread"
    size="small"
    @update:selection="emit('selected', $event)"
    @sort="onSort"
  >
    <Column
      field="name"
      :header="t('thread.list.name')"
      sortable
    />
    <Column
      field="agents"
      :header="t('thread.list.agents')"
    >
      <template #body="{ data }">
        <AvatarGroup>
          <Avatar
            v-for="agent in data.agents"
            :key="agent.agent_id + agent.agent_class"
            v-tooltip="agent.agent_config.name"
          >
            <template #icon>
              <Icon
                :name="agent.agent_config.icon"
                size="xl"
              />
            </template>
          </Avatar>
        </AvatarGroup>
      </template>
    </Column>
    <Column
      field="users"
      :header="t('thread.users')"
    >
      <template #body="{ data }">
        <AvatarGroup>
          <Avatar
            v-for="user in data.users"
            :key="user.id"
            v-tooltip="user.name"
            :image="user?.profile_image ?? undefined"
            :label="!user?.profile_image ? initials(user) : undefined"
            shape="circle"
          />
        </AvatarGroup>
      </template>
    </Column>
    <Column
      field="created_at"
      :header="t('thread.list.created')"
      sortable
    >
      <template #body="{ data }">
        <p>{{ formatted(data.created_at) }}</p>
      </template>
    </Column>
    <Column
      field="num_turns"
      :header="t('thread.list.numTurns')"
    >
      <template #body="{ data }">
        <Badge :value="data.num_turns" />
      </template>
    </Column>
    <Column
      field="num_events"
      :header="t('thread.list.numEvents')"
    >
      <template #body="{ data }">
        <Badge :value="data.num_events" />
      </template>
    </Column>
    <Column
      field="has_errors"
      :header="t('thread.list.status')"
    >
      <template #body="{ data }">
        <Tag
          v-if="data.has_errors"
          severity="danger"
          :value="t('event.list.error')"
        />
        <Tag
          v-else
          severity="success"
          :value="t('event.list.successful')"
        />
      </template>
    </Column>
    <Column
      field="has_errors"
      :header="t('thread.list.pending')"
    >
      <template #body="{ data }">
        <Tag
          v-if="data.has_pending"
          severity="warn"
          :value="pendingType(data)"
        />
        <Tag
          v-else
          severity="success"
          :value="t('event.list.no')"
        />
      </template>
    </Column>
  </DataTable>
</template>

<script setup lang="ts">
import type { ThreadDto, MinimalUserDto } from '@core/sdk/client'
import type { DataTableSortEvent } from 'primevue'

const route = useRoute()
const { t } = useI18n()

const props = defineProps<{
  threads: ThreadDto[]
  sortField: string
  sortOrder: 1 | -1
}>()

const emit = defineEmits<{
  selected: [thread: ThreadDto]
  sort: [payload: { field: string, order: 1 | -1 }]
}>()

const onSort = (event: DataTableSortEvent) => {
  emit('sort', {
    field: event.sortField as string,
    order: (event.sortOrder ?? -1) as 1 | -1,
  })
}

const initials = (user: MinimalUserDto) => user.name?.split(' ').map(n => n[0]).join('')
const formatted = (datestr: string) => useDateFormat(new Date(datestr), 'DD.MM.YYYY HH:mm:ss')
const { pendingType } = useThreadUtils()

const selectedThread = computed(() => {
  return props.threads.filter((thread: ThreadDto) => {
    return thread.id === route.params.thread_id
  })
})
</script>
