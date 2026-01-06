<template>
  <StructuralScreen>
    <StructuralColumn
      :title="t('agent.title')"
      :loading="agentsAreLoading"
    >
      <div class="flex flex-col gap-4">
        <div class="flex w-full justify-end">
          <Button
            :label="t('agent.create.button')"
            icon="pi pi-plus"
            @click="createModalOpen = true"
          />
        </div>
        <div class="grid grid-cols-2 gap-4 2xl:grid-cols-2">
          <AgentCard
            v-for="agent in agents"
            :key="agent.agent_id"
            :agent="agent"
            @click="() => toAgent(agent)"
          />
        </div>
      </div>
      <AgentCreateModal
        v-model="createModalOpen"
        @success="handleCreateSuccess"
      />
    </StructuralColumn>

    <NuxtPage />
  </StructuralScreen>
</template>

<script setup lang="ts">
import type { AgentDto } from '@core/sdk/client'

import { useLocalePath } from '#i18n'

const router = useRouter()
const localePath = useLocalePath()
const { t } = useI18n()

const { agents, agentsAreLoading } = useAgents()

const createModalOpen = ref(false)

const toAgent = (agent: AgentDto) => {
  router.push(localePath(`/service/agents/${agent.agent_class}-${agent.agent_id}/overview`))
}

const handleCreateSuccess = (agentClass: string, agentId: string) => {
  // Navigate to the newly created agent
  router.push(localePath(`/service/agents/${agentClass}-${agentId}/overview`))
}
</script>
