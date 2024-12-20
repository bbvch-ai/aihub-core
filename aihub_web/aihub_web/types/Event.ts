export interface EventData {
  event_id: string
  created_at: number
  _type: string
}

export interface BaseEvent {
  _type: string
  event_id: string
  created_at: number
}
