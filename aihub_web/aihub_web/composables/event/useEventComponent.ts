import type { AgentEventReadable } from '@core/sdk/client'

import {
  EventDisplayAgentInTheLoopRequestEvent,
  EventDisplayAgentInTheLoopResponseEvent,
  EventDisplayChunkEvent,
  EventDisplayDocumentChangedEvent,
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
  EventDisplayToolErrorEvent,
  EventDisplayToolEvent,
  EventDisplayToolOutputEvent,
  EventDisplayUnknownEvent,
  EventDisplayUserMessageEvent,
  EventDisplayGuardEvent,
  EventDisplayGuardAcceptEvent,
  EventDisplayGuardRejectionEvent,
  EventDisplayRouterEvent,
  EventDisplayExceptionEvent,
} from '#components'

export const useEventComponent = () => {
  const resolveComponentForEvent = (event: AgentEventReadable) => {
    const mapping = {
      UserMessageEvent: EventDisplayUserMessageEvent,
      ChunkEvent: EventDisplayChunkEvent,
      LLMEvent: EventDisplayLLMEvent,
      LLMCostEvent: EventDisplayLLMCostEvent,
      LimitChatHistoryEvent: EventDisplayLimitChatHistoryEvent,
      ThoughtEvent: EventDisplayThoughtEvent,
      EmbeddingEvent: EventDisplayEmbeddingEvent,
      RerankerEvent: EventDisplayRerankerEvent,
      RetrieverEvent: EventDisplayRetrieverEvent,
      DocumentChangedEvent: EventDisplayDocumentChangedEvent,
      StandaloneQuestionCondenserEvent: EventDisplayStandaloneQuestionCondenserEvent,
      ToolEvent: EventDisplayToolEvent,
      ToolOutputEvent: EventDisplayToolOutputEvent,
      ToolErrorEvent: EventDisplayToolErrorEvent,
      AgentInTheLoopRequestEvent: EventDisplayAgentInTheLoopRequestEvent,
      AgentInTheLoopResponseEvent: EventDisplayAgentInTheLoopResponseEvent,
      HumanInTheLoopRequestEvent: EventDisplayHumanInTheLoopRequestEvent,
      HumanInTheLoopResponseEvent: EventDisplayHumanInTheLoopResponseEvent,
      GuardEvent: EventDisplayGuardEvent,
      GuardAcceptEvent: EventDisplayGuardAcceptEvent,
      GuardRejectionEvent: EventDisplayGuardRejectionEvent,
      AgentSuitabilityAcceptEvent: EventDisplayGuardAcceptEvent,
      AgentSuitabilityRejectEvent: EventDisplayGuardRejectionEvent,
      ContextSufficientAcceptEvent: EventDisplayGuardAcceptEvent,
      ContextInsufficientRejectEvent: EventDisplayGuardRejectionEvent,
      FewShotAcceptEvent: EventDisplayGuardAcceptEvent,
      FewShotRejectEvent: EventDisplayGuardRejectionEvent,
      SensitiveInfoAcceptEvent: EventDisplayGuardAcceptEvent,
      SensitiveInfoRejectEvent: EventDisplayGuardRejectionEvent,
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
