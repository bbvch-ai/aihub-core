Feature: Retrieval Agent
  Testing the RetrievalAgent

  Scenario: Test RetrievalAgent to ensure it retrieves relevant documents and combines them
    Given a RetrievalAgent and a vector store with 3 documents about AI
    When the user asks "What is AI?"
    Then the agent should retrieve "3" nodes
    * the nodes should be combined into a single message
    * the agent returns an event with this context message and stops
