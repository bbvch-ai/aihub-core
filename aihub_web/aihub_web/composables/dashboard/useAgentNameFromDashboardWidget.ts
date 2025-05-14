import type { AgentDto } from '@core/sdk/client'
import type { DashboardWidget } from '@core/types/DashboardWidget'

export const useAgentNameFromDashboardWidget = (widgetData: DashboardWidget) => {
  const { agents } = useAgents()
  const { t } = useI18n()
  const agentName = computed<string>(() => {
    const agentId = widgetData.agent?.agentId
    const agentClass = widgetData.agent?.agentClass
    if (!(agentId && agentClass)) {
      return t('dashboard.all_agents')
    }
    if (agentClass === 'UserAgent') {
      return t('dashboard.users')
    }
    const agent = agents.value?.find((agent: AgentDto) => {
      return agent.agent_id === agentId && agent.agent_class === agentClass
    })
    if (!agent) {
      return t('dashboard.unknown_agent')
    }
    return agent.agent_config.name
  })
  return {
    agentName,
  }
}
