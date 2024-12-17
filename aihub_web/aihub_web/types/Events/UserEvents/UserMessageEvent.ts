import type { BaseEvent } from '@core/types/Event'

export interface ChatMessage {
  role: string
  content: string
}

export interface UserMessageEvent extends BaseEvent {
  locale: string
  messages: ChatMessage[]
}
