Feature: Expert RAG Agent
  Testing the ExpertRAGAgent workflow with mandatory expert escalation

  Scenario: Test ExpertRAGAgent handles user declining expert escalation
    Given an ExpertRAGAgent runner
    When a query is sent and user declines expert escalation with query "What is quantum entanglement in advanced medicine?"
    Then a HumanInTheLoopConfirmationRequestEvent is present
    * an ExpertRejectEvent is present
    * an LLMEvent is present with a generated response
    * a StopEvent is present

  Scenario: Test ExpertRAGAgent expert escalation when user accepts
    Given an ExpertRAGAgent runner
    When a query is sent and user accepts expert escalation with query "What is quantum entanglement in advanced medicine?"
    Then a HumanInTheLoopConfirmationRequestEvent is present
    * a UserRequestsExpertEvent is present
    * an AgentInTheLoopRequestEvent is present
    * an LLMEvent is present with a generated response
    * a StopEvent is present
