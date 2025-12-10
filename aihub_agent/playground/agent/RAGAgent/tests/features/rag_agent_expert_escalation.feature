Feature: RAG Agent Expert Escalation
  Testing the RAGAgent expert escalation workflow with ExpertAskingAgent

  Scenario: Test RAGAgent handles user declining expert escalation
    Given a RAGAgent runner with expert escalation enabled
    When a query is sent and user declines expert escalation with query "What is quantum entanglement in advanced medicine?"
    Then a HumanInTheLoopConfirmationRequestEvent is present
    * an ExpertRejectEvent is present
    * an LLMEvent is present with a generated response
    * a StopEvent is present

  Scenario: Test RAGAgent expert escalation user accepts
    Given a RAGAgent runner with expert escalation enabled
    When a query is sent and user accepts expert escalation with query "What is quantum entanglement in advanced medicine?"
    Then a HumanInTheLoopConfirmationRequestEvent is present
    * a UserRequestsExpertEvent is present
    * an AgentInTheLoopRequestEvent is present
    * an LLMEvent is present with a generated response
    * a StopEvent is present
