import type { AgentEventReadable } from '@core/sdk/client'

import {
  EventDisplayAgentInTheLoopRequestEvent,
  EventDisplayAgentInTheLoopResponseEvent,
  EventDisplayChunkEvent,
  EventDisplayEmbeddingEvent,
  EventDisplayHumanInTheLoopRequestEvent,
  EventDisplayHumanInTheLoopResponseEvent,
  EventDisplayLLMCostEvent,
  EventDisplayLLMEvent,
  EventDisplayLimitChatHistoryEvent,
  EventDisplayRerankerEvent,
  EventDisplayRetrieverEvent,
  EventDisplayStandaloneQuestionCondenserEvent,
  EventDisplayStopEvent,
  EventDisplayThoughtEvent,
  EventDisplayToolEvent,
  EventDisplayUnknownEvent,
  EventDisplayUserMessageEvent,
  EventDisplayGuardEvent,
  EventDisplayRouterEvent,
  EventDisplayExceptionEvent,
} from '#components'

export const useEventComponent = () => {
  const resolveComponentForEvent = (event: AgentEventReadable) => {
    const mapping = {
      UserMessageEvent: EventDisplayUserMessageEvent,
      ChunkEventReadable: EventDisplayChunkEvent,
      LLMEvent: EventDisplayLLMEvent,
      LLMCostEvent: EventDisplayLLMCostEvent,
      LimitChatHistoryEvent: EventDisplayLimitChatHistoryEvent,
      ThoughtEvent: EventDisplayThoughtEvent,
      EmbeddingEvent: EventDisplayEmbeddingEvent,
      RerankerEvent: EventDisplayRerankerEvent,
      RetrieverEvent: EventDisplayRetrieverEvent,
      StandaloneQuestionCondenserEvent: EventDisplayStandaloneQuestionCondenserEvent,
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
