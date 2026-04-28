import type { ContextualizedAgentEvent } from '@core/sdk/client'

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
  EventDisplayGroundedRAGStopEvent,
  EventDisplayUngroundedRAGStopEvent,
  EventDisplayStopEvent,
  EventDisplayThoughtEvent,
  EventDisplayToolEvent,
  EventDisplayUnknownEvent,
  EventDisplayUserMessageEvent,
  EventDisplayRAGStartEvent,
  EventDisplayGuardEvent,
  EventDisplayGuardAcceptEvent,
  EventDisplayGuardRejectionEvent,
  EventDisplayRouterEvent,
  EventDisplayExceptionEvent,
  EventDisplayBaseRetrieveMemoryEvent,
  EventDisplayBaseStoreMemoryEvent,
  EventDisplayAddMemoryToChatHistoryEvent,
} from '#components'

export const useEventComponent = () => {
  const resolveComponentForEvent = (event: ContextualizedAgentEvent) => {
    const mapping = {
      UserMessageEvent: EventDisplayUserMessageEvent,
      RAGStartEvent: EventDisplayRAGStartEvent,
      ChunkEvent: EventDisplayChunkEvent,
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
      GroundedRAGStopEvent: EventDisplayGroundedRAGStopEvent,
      UngroundedRAGStopEvent: EventDisplayUngroundedRAGStopEvent,
      StopEvent: EventDisplayStopEvent,
      RouterEvent: EventDisplayRouterEvent,
      ExceptionEvent: EventDisplayExceptionEvent,
      BaseRetrieveMemoryEvent: EventDisplayBaseRetrieveMemoryEvent,
      BaseStoreMemoryEvent: EventDisplayBaseStoreMemoryEvent,
      AddMemoryToChatHistoryEvent: EventDisplayAddMemoryToChatHistoryEvent,
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
