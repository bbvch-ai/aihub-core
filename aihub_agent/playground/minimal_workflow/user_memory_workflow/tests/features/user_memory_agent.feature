Feature: UserMemoryAgent - Memory-Enhanced Conversational Agent
  As a user
  I want the agent to remember information from previous conversations
  So that I can have personalized, context-aware interactions

  Background:
    Given a UserMemoryAgent runner with valid configuration

  Scenario: Full memory workflow - retrieve, extend, respond, persist
    Given pre-seeded memory: "User's favorite programming language is Python"
    When the start event is sent with user query "What is my favorite programming language?"
    Then a RetrieveUserMemoryEvent is present with 1 or more memories or relations
    And the memory or relation content contains "Python"
    And an AddMemoryToChatHistoryEvent is present
    And the extended history has a system message with memory context
    And the memory system message is after any existing system messages
    And an LLMEvent is present
    And the LLM response mentions "Python"
    And a StoreUserMemoryEvent is present with memory updates
    And a StopEvent is present

  Scenario: Agent with no existing memories
    Given no pre-seeded memories
    When the start event is sent with user query "Hello, my name is Alice and I work as a software engineer"
    Then a RetrieveUserMemoryEvent is present
    And an AddMemoryToChatHistoryEvent is present
    And an LLMEvent is present
    And a StoreUserMemoryEvent is present with memory updates
    And a StopEvent is present

  Scenario: Locale-specific memory formatting
    Given a UserMemoryAgent runner with locale "de"
    And pre-seeded memory: "Benutzer bevorzugt kurze Antworten"
    When the start event is sent with user query "Was ist KI?" and locale "de"
    Then an AddMemoryToChatHistoryEvent is present
    And the memory system message uses German formatting
    And the memory system message contains "Die folgenden Informationen"
