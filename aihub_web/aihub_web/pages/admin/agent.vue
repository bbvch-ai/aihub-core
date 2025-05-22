<template>
  <StructuralScreen>
    <StructuralColumn
      :title="t('agent.title')"
      :loading="agentsAreLoading"
    >
      <div
        class="grid grid-cols-2 gap-4 2xl:grid-cols-2"
      >
        <AgentCard
          v-for="agent in agents"
          :key="agent.agent_id"
          :agent="agent"
          @click="() => toAgent(agent)"
        />
      </div>
    </StructuralColumn>

    <NuxtPage />
  </StructuralScreen>
</template>

<script setup lang="ts">
import type { AgentDto } from '@core/sdk/client'
import type { NavItem } from '@core/types/NavItem'

import { useLocalePath } from '#i18n'

const route = useRoute()
const router = useRouter()
const localePath = useLocalePath()
const { t } = useI18n()

const { agents, agentsAreLoading } = useAgents()

const toAgent = (agent: AgentDto) => {
  router.push(localePath(`/admin/agent/agent-${agent.agent_id}-${agent.agent_class}/overview`))
}
</script>
