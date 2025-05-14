import type { AgentDto } from '@core/sdk/client'
import type { DashboardWidget } from '@core/types/DashboardWidget'

export const useAgentNameFromDashboardWidget = (widgetData: DashboardWidget) => {
  const { agents } = useAgents()
  const agentName = computed<string>(() => {
    const agentId = widgetData.agent?.agentId
    const agentClass = widgetData.agent?.agentClass
    if (!(agentId && agentClass)) {
      return 'All Agents'
    }
    if (agentClass === 'UserAgent') {
      return 'AI-Hub Users'
    }
    const agent = agents.value?.find((agent: AgentDto) => {
      return agent.agent_id === agentId && agent.agent_class === agentClass
    })
    if (!agent) {
      return 'Unknown Agent'
    }
    return agent.agent_config.name
  })
  return {
    agentName,
  }
}
