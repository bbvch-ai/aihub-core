import type { BaseEvent } from '@core/types/Event'

export interface UserMessageEvent extends BaseEvent {
  content: string
}
