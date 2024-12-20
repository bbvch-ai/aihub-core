import type { AgentConfig } from '@core/types/agent/AgentConfig'
import type { StartEventSpecs } from '@core/types/Events/start_event/StartEventSpecs'

export interface Agent {
  agent_class: string
  agent_id: string
  agent_config: AgentConfig
  start_events: StartEventSpecs[]
}
