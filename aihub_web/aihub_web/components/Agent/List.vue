<template>
  <DataTable
    :value="agents"
    size="small"
    table-style="min-width: 50rem"
    selection-mode="single"
    @update:selection="emit('selected', $event)"
  >
    <Column
      field="agent_config.name"
      :header="t('agent.list.name')"
    />
    <Column
      field="agent_config.description"
      :header="t('agent.list.description')"
    >
      <template #body="{ data }">
        <span class="text-xs">
          {{ data.agent_config.description }}
        </span>
      </template>
    </Column>
    <Column
      field="agent_id"
      :header="t('agent.list.agent')"
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
      :header="t('agent.list.is_conversational')"
    >
      <template #body="{ data }">
        <Badge
          :value="data.is_conversational ? t('agent.list.true') : t('agent.list.false')"
        />
      </template>
    </Column>
    <Column
      field="is_online"
      :header="t('agent.list.status')"
    >
      <template #body="{ data }">
        <Tag
          v-if="data.is_online"
          severity="success"
          :value="t('agent.list.online')"
        />
        <Tag
          v-else
          severity="danger"
          :value="t('agent.list.offline')"
        />
      </template>
    </Column>
  </DataTable>
</template>

<script setup lang="ts">
import type { FullAgentInstanceDto } from '@core/sdk/client'

defineProps<{
  agents: FullAgentInstanceDto[]
}>()

const { t } = useI18n()

const emit = defineEmits<{
  selected: [AGENT: FullAgentInstanceDto]
}>()
</script>
