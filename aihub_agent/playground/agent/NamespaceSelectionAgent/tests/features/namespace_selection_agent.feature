Feature: Namespace Selection Agent
  Testing the NamespaceSelectionAgent that asks users to select namespaces and delegates to RAG agent.

  Scenario: Test first message triggers namespace selection question
    Given a NamespaceSelectionAgent runner with mocked buckets and namespaces
    When the user sends a message "What documents do you have?"
    Then a HumanInTheLoopChatRequestEvent is present
    * the chat request message asks about namespace selection

  Scenario: Test user selection is parsed and stored
    Given a NamespaceSelectionAgent runner with mocked buckets and namespaces
    When the user sends a message and selects "hr" namespace
    Then the namespace selection is stored in ThreadContext
    * an AgentInTheLoopRequestEvent is present for RAGAgent

  Scenario: Test subsequent messages delegate to RAG agent
    Given a NamespaceSelectionAgent runner with existing namespace selection
    When the user sends a subsequent message "Tell me about vacation policies"
    Then an AgentInTheLoopRequestEvent is present for RAGAgent
    * the RAGUserMessageEvent includes namespace overrides
