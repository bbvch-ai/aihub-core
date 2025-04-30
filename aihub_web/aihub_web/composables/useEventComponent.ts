import type { ExceptionEvent, WsServerEvent } from '@core/sdk/client'

import {
  EventDisplayAgentInTheLoopRequestEvent,
  EventDisplayAgentInTheLoopResponseEvent,
  EventDisplayChunkEvent,
  EventDisplayEmbeddingEvent,
  EventDisplayHumanInTheLoopRequestEvent,
  EventDisplayHumanInTheLoopResponseEvent,
  EventDisplayLLMCostEvent,
  EventDisplayLLMEvent,
  EventDisplayRerankerEvent,
  EventDisplayRetrieverEvent,
  EventDisplayStopEvent,
  EventDisplayThoughtEvent,
  EventDisplayToolEvent,
  EventDisplayUnknownEvent,
  EventDisplayUserMessageEvent,
  EventDisplayGuardEvent,
  EventDisplayRouterEvent, EventDisplayExceptionEvent,
} from '#components'

export default () => {
  const resolveComponentForEvent = (event: WsServerEvent) => {
    const mapping = {
      UserMessageEvent: EventDisplayUserMessageEvent,
      ChunkEvent: EventDisplayChunkEvent,
      LLMEvent: EventDisplayLLMEvent,
      LLMCostEvent: EventDisplayLLMCostEvent,
      ThoughtEvent: EventDisplayThoughtEvent,
      EmbeddingEvent: EventDisplayEmbeddingEvent,
      RerankerEvent: EventDisplayRerankerEvent,
      RetrieverEvent: EventDisplayRetrieverEvent,
      ToolEvent: EventDisplayToolEvent,
      AgentInTheLoopRequestEvent: EventDisplayAgentInTheLoopRequestEvent,
      AgentInTheLoopResponseEvent: EventDisplayAgentInTheLoopResponseEvent,
      HumanInTheLoopRequestEvent: EventDisplayHumanInTheLoopRequestEvent,
      HumanInTheLoopResponseEvent: EventDisplayHumanInTheLoopResponseEvent,
      GuardEvent: EventDisplayGuardEvent,
      StopEvent: EventDisplayStopEvent,
      RouterEvent: EventDisplayRouterEvent,
      ExceptionEvent: EventDisplayExceptionEvent,
    }
    const exact_match = mapping[event.event._event_name]
    if (exact_match) {
      return exact_match
    }
    for (const eventName in mapping) {
      if (event.event._parent_event_names.includes(eventName)) {
        return mapping[eventName]
      }
    }
    return EventDisplayUnknownEvent
  }
  return {
    resolveComponentForEvent,
  }
}
