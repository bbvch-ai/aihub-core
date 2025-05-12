<template>
  <div>
    <DataTable
      :value="agents"
      table-style="min-width: 50rem"
      selection-mode="single"
      @update:selection="emit('selected', $event)"
    >
      <Column
        field="agent_config.name"
        header="Name"
      />
      <Column
        field="agent_config.description"
        header="Description"
      >
        <template #body="{ data }">
          <span class="text-xs">
            {{ data.agent_config.description }}
          </span>
        </template>
      </Column>
      <Column
        field="agent_id"
        header="Agent"
      >
        <template #body="{ data }">
          <AvatarGroup>
            <Avatar
              :key="data.agent_id + data.agent_class"
              v-tooltip="data.agent_config.name"
            >
              <template #icon>
                <Icon
                  :name="data.agent_config.icon"
                  size="xl"
                />
              </template>
            </Avatar>
          </AvatarGroup>
        </template>
      </Column>
      <Column
        field="is_conversational"
        header="Conversational"
      >
        <template #body="{ data }">
          <Badge :value="data.is_conversational" />
        </template>
      </Column>
      <Column
        field="is_online"
        header="Status"
      >
        <template #body="{ data }">
          <Tag
            v-if="data.is_online"
            severity="success"
            value="Online"
          />
          <Tag
            v-else
            severity="danger"
            value="Offline"
          />
        </template>
      </Column>
    </DataTable>
  </div>
</template>

<script setup lang="ts">
import type { AgentDto } from '@core/sdk/client'

const { t } = useI18n()

defineProps<{
  agents: AgentDto[]
}>()

const emit = defineEmits<{
  selected: [AGENT: AgentDto]
}>()
</script>

<style scoped>

</style>
