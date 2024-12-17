import { useMutation, useQuery } from '@pinia/colada'
import { defineStore } from 'pinia'
import { computed } from 'vue'
import type { Agent } from '@core/types/agent/Agent'

export const useAgentsStore = defineStore('agents', () => {
  const { getHeaders } = useAuth()

  // Fetch all agents from the discovery endpoint
  const {
    data: agents,
    state: agentsLoadingState,
    refresh: refreshAgents,
    refetch: refetchAgents,
  } = useQuery<Agent[]>({
    key: ['agents'],
    staleTime: 1000 * 60 * 5, // 5 minutes
    enabled: true,
    query: async () => {
      const headers = await getHeaders()
      const res = await fetch(`/api/v1/agent/discover`, { headers })
      if (!res.ok) {
        throw new Error(`Failed to fetch agents: ${res.statusText}`)
      }
      return res.json() as Promise<Agent[]>
    },
  })

  // Create a map for easy lookup.
  // We'll use `<agent_class>:<agent_id>` as a key since each agent is identified by those two fields.
  const agentMap = computed(() => {
    const map: Record<string, Agent> = {}
    agents.value?.forEach((agent) => {
      const key = `${agent.agent_class}:${agent.agent_id}`
      map[key] = agent
    })
    return map
  })

  // Helper to replace or insert an agent in the agents array.
  function replaceAgent(updatedAgent: Agent) {
    if (!agents.value) return
    const key = (a: Agent) => `${a.agent_class}:${a.agent_id}`
    const updatedKey = key(updatedAgent)

    const index = agents.value.findIndex(a => key(a) === updatedKey)
    if (index !== -1) {
      agents.value.splice(index, 1, updatedAgent)
    }
    else {
      // If not found, add it
      agents.value.push(updatedAgent)
    }
  }

  // Fetch a single agent by class and ID
  const { mutate: fetchAgentById } = useMutation({
    mutation: async (payload: { agentClass: string, agentId: string }) => {
      const headers = await getHeaders()
      const res = await fetch(`/api/v1/agent/${payload.agentClass}/${payload.agentId}`, { headers })
      if (!res.ok) {
        throw new Error(`Failed to fetch agent: ${res.statusText}`)
      }
      return res.json() as Promise<Agent>
    },
    onSuccess(agent) {
      replaceAgent(agent)
    },
  })

  return {
    agents,
    agentsLoadingState,
    refreshAgents,
    refetchAgents,
    agentMap,
    fetchAgentById,
  }
})
