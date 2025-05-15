<template>
  <div
    class="flex flex-col gap-3"
  >
    <div class="flex w-full">
      <div class="flex w-1/2 flex-col gap-2">
        <h3 class="font-bold">
          {{ t('thread.users') }}
        </h3>
        <UserAvatar
          v-for="user in users"
          :key="user.id"
          :user="user"
        />
      </div>
      <div class="flex w-1/2 flex-col gap-2">
        <h3 class="font-bold">
          {{ t('thread.assistants') }}
        </h3>
        <AgentAvatar
          v-for="agent in agents"
          :key="agent.agent_class + agent.agent_id"
          :agent="agent"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { AgentDto, ThreadDto, UserDto } from '@core/sdk/client'

const { t } = useI18n()

const props = defineProps<{
  thread: ThreadDto
}>()

const users = computed<UserDto[]>(() => props.thread.users ?? [])
const agents = computed<AgentDto[]>(() => props.thread.agents ?? [])
</script>
