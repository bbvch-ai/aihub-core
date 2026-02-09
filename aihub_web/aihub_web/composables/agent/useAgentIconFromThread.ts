import type { MinimalAgentInstanceDto, ThreadDto, ContextualizedAgentEvent } from '@core/sdk/client'

export default (event: ContextualizedAgentEvent, thread: ThreadDto) => {
  return computed<string | undefined>(() => thread.participating_agents
    ?.find((agent: MinimalAgentInstanceDto) => agent.agent_id == event.agent_id && agent.agent_class == event.agent_class)
    ?.agent_config?.icon,
  )
}
