import type { MinimalAgentDto, ThreadDto, WsServerEvent } from '@core/sdk/client'

export default (event: WsServerEvent, thread: ThreadDto) => {
  return computed<string | undefined>(() => thread.participating_agents
    ?.find((agent: MinimalAgentDto) => agent.agent_id == event.agent_id && agent.agent_class == event.agent_class)
    ?.agent_config?.icon,
  )
}
