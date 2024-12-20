import type { LocaleString } from '@core/types/i18n/LocaleString'

export interface AgentConfig {
  agent_id: string
  name: LocaleString
  description: LocaleString
  system_prompt: LocaleString
  color?: string
  voice?: string
}
