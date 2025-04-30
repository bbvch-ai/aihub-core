<template>
  <div class="card">
    <DataTable
      :value="threads"
      table-style="min-width: 50rem"
      selection-mode="single"
      @update:selection="emit('selected', $event)"
    >
      <Column
        field="name"
        header="Name"
      />
      <Column
        field="agents"
        header="Agents"
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
        header="Users"
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
        field="Created"
        header="Created"
      >
        <template #body="{ data }">
          <p>{{ formatted(data.created_at) }}</p>
        </template>
      </Column>
      <Column
        field="num_turns"
        header="Number of Turns"
      >
        <template #body="{ data }">
          <Badge :value="data.num_turns" />
        </template>
      </Column>
      <Column
        field="num_events"
        header="Number of Events"
      >
        <template #body="{ data }">
          <Badge :value="data.num_events" />
        </template>
      </Column>
      <Column
        field="has_errors"
        header="Status"
      >
        <template #body="{ data }">
          <Tag
            v-if="data.has_errors"
            severity="danger"
            value="Error"
          />
          <Tag
            v-else
            severity="success"
            value="Successfull"
          />
        </template>
      </Column>
      <Column
        field="has_errors"
        header="Pending"
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
            value="No"
          />
        </template>
      </Column>
    </DataTable>
  </div>
</template>

<script setup lang="ts">
import useThreadUtils from '@core/composables/useThreadUtils'

import type { ThreadDto, UserDto } from '@core/sdk/client'

defineProps<{
  threads: ThreadDto[]
}>()

const emit = defineEmits<{
  selected: [thread: ThreadDto]
}>()

const initials = (user: UserDto) => user.name?.split(' ').map(n => n[0]).join('')
const formatted = (datestr: string) => useDateFormat(new Date(datestr), 'DD.MM.YYYY HH:mm:ss')
const { pendingType } = useThreadUtils()
</script>

<style scoped>

</style>
