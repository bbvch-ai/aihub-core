<template>
  <DataTable
    :value="walkthroughs"
    table-style="min-width: 50rem"
    selection-mode="single"
    :selection="selectedWalkthrough"
    size="small"
    @update:selection="emit('selected', $event)"
  >
    <Column
      field="Created"
      :header="t('process.walkthrough.list.created')"
    >
      <template #body="{ data }">
        <p>{{ formatted(data.created_at) }}</p>
      </template>
    </Column>
    <Column
      field="agents"
      :header="t('process.walkthrough.list.agents')"
    >
      <template #body="{ data }">
        <AvatarGroup>
          <Avatar
            v-for="agent in data.involved_agents"
            :key="agent.agent_id + agent.agent_class"
            v-tooltip.top="agent.agent_config.name"
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
      :header="t('process.walkthrough.list.users')"
    >
      <template #body="{ data }">
        <AvatarGroup>
          <Avatar
            v-for="user in data.involved_humans"
            :key="user.id"
            v-tooltip.top="user.name"
            :image="user?.profile_image ?? undefined"
            :label="!user?.profile_image ? initials(user) : undefined"
            shape="circle"
          />
        </AvatarGroup>
      </template>
    </Column>
    <Column
      field="updated_at"
      :header="t('process.walkthrough.list.updated')"
    >
      <template #body="{ data }">
        <Tag
          :value="getTimeAgo(data.updated_at / 1000000).text"
          :severity="getTimeAgo(data.updated_at / 1000000).severity"
        />
      </template>
    </Column>
    <Column
      field="process_steps"
      :header="t('process.walkthrough.list.steps')"
    >
      <template #body="{ data }">
        <div class="relative flex w-fit flex-row gap-3">
          <div class="absolute inset-x-12 top-4 border-t-4 border-dotted border-gray-400/50" />
          <div
            v-for="step in data.process_steps"
            :key="step.step_index"
            class="z-50 flex w-24 flex-col items-center justify-center gap-1"
          >
            <Avatar
              v-tooltip.top="tooltipForStep(step)"
              :class="{
                'bg-green-200 text-green-800 dark:bg-green-800 dark:text-green-100': step.is_completed,
              }"
              shape="circle"
              size="normal"
            >
              <Icon
                :name="iconForStep(step)"
                size="small"
              />
            </Avatar>
            <p class="w-full truncate text-center text-xs">
              {{ nameForStep(step) }}
            </p>
          </div>
        </div>
      </template>
    </Column>
  </DataTable>
</template>

<script setup lang="ts">
import type {
  AgentProcessStepDto,
  HumanProcessStepDto,
  MinimalUserDto,
  ProcessWalkthroughDto,
  ProgramProcessStepDto,
} from '@core/sdk/client'

type ProcessStepDto = AgentProcessStepDto | ProgramProcessStepDto | HumanProcessStepDto

const props = defineProps<{
  walkthroughs: ProcessWalkthroughDto[]
}>()

const emit = defineEmits<{
  selected: [walkthrough: ProcessWalkthroughDto]
}>()

const { t } = useI18n()
const route = useRoute()
const { getTimeAgo } = useTimeAgo()

const iconForStep = (process_step: ProcessStepDto) => {
  if (process_step.step_type === 'human') {
    return 'mage:user'
  }
  if (process_step.step_type === 'program') {
    return 'tdesign:code'
  }
  if (process_step.step_type === 'agent') {
    return process_step.work_request?.agent_info?.agent_config?.icon ?? process_step.work_response?.agent_info?.agent_config?.icon ?? 'meteor-icons:robot'
  }
}
const tooltipForStep = (process_step: ProcessStepDto) => {
  if (process_step.step_type === 'human' && process_step.work_response) {
    return process_step.work_response.data.submitted_by.email
  }
  if (process_step.step_type === 'program') {
    return ''
  }
  if (process_step.step_type === 'agent') {
    if (process_step.work_request) {
      return process_step.work_request?.agent_info?.agent_config?.name
    }
    return process_step.work_response?.agent_info?.agent_config?.name
  }
}
const nameForStep = (process_step: ProcessStepDto) => {
  return process_step.work_response?.event_name ?? process_step.work_request?.event_name
}

const initials = (user: MinimalUserDto) => user.name?.split(' ').map(n => n[0]).join('')
const formatted = (timestamp: number) => useDateFormat(new Date(timestamp / 1000000), 'DD.MM.YYYY HH:mm:ss')

const selectedWalkthrough = computed(() => {
  return props.walkthroughs.filter((walkthrough: ProcessWalkthroughDto) => {
    return walkthrough.process_walkthrough_id === route.params.process_walkthrough_id
  })
})
</script>
