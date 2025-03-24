import { type AgentDto, discoverAgents } from '@core/sdk/client'
import { useQuery } from '@pinia/colada'
import { defineStore } from 'pinia'
import { computed } from 'vue'

export const useAgentsStore = defineStore('agents', () => {
  // Fetch all agents from the discovery endpoint
  const {
    data: agents,
    state: agentsLoadingState,
    refresh: refreshAgents,
    refetch: refetchAgents,
  } = useQuery<AgentDto[]>({
    key: ['agents'],
    staleTime: 1000 * 60 * 5, // 5 minutes
    enabled: true,
    query: async () => {
      return await discoverAgents({
        composable: '$fetch',
      })
    },
  })

  // Create a map for easy lookup.
  // We'll use `<agent_class>:<agent_id>` as a key since each agent is identified by those two fields.
  const agentMap = computed(() => {
    const map: Record<string, AgentDto> = {}
    agents.value?.forEach((agent) => {
      const key = `${agent.agent_class}:${agent.agent_id}`
      map[key] = agent
    })
    return map
  })

  return {
    agents,
    agentsLoadingState,
    refreshAgents,
    refetchAgents,
    agentMap,
  }
})
