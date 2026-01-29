<template>
  <DataTable
    :value="users"
    table-style="min-width: 50rem"
    selection-mode="single"
    :selection="selectedUser"
    size="small"
    @update:selection="emit('selected', $event)"
  >
    <Column
      field="profile_image"
      :header="t('user.list.avatar')"
    >
      <template #body="{ data }">
        <Avatar
          v-tooltip="data.name"
          :image="data?.profile_image ?? undefined"
          :label="!data?.profile_image ? initials(data) : undefined"
          shape="circle"
        />
      </template>
    </Column>
    <Column
      field="name"
      :header="t('user.list.name')"
    />
    <Column
      field="email"
      :header="t('user.list.email')"
    />
    <Column
      field="last_accessed"
      :header="t('user.list.last_accessed')"
    >
      <template #body="{ data }">
        <Tag
          v-if="data.last_accessed"
          :value="getTimeAgo(data.last_accessed).text"
          :severity="getTimeAgo(data.last_accessed).severity"
        />
      </template>
    </Column>
    <Column
      field="roles"
      :header="t('user.list.roles')"
    >
      <template #body="{ data }">
        <div class="flex flex-wrap gap-2">
          <Badge
            v-for="role in data.roles"
            :key="role"
            :value="role"
          />
        </div>
      </template>
    </Column>
  </DataTable>
</template>

<script setup lang="ts">
import type { UserDto } from '@core/sdk/client'

const route = useRoute()
const { t } = useI18n()
const { getTimeAgo } = useTimeAgo()

const props = defineProps<{
  users: UserDto[]
}>()

const emit = defineEmits<{
  selected: [user: UserDto]
}>()

const initials = (user: UserDto) => user.name?.split(' ').map(n => n[0]).join('')

const selectedUser = computed(() => {
  return props.users.filter((user: UserDto) => {
    return user.id === route.params.user_id
  })
})
</script>
