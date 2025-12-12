Feature: Insight Retrieval Agent
  Testing the InsightRetrievalAgent for MongoDB insight retrieval

  Scenario: Test InsightRetrievalAgent retrieves expert insights
    Given an InsightRetrievalAgent with insight sources configured
    * test insights are pre-seeded in the database
    When the user asks "What is machine learning?"
    Then a RetrieverEvent is present with retrieved insight nodes
    * the nodes should be combined into a single message
    * the agent returns an insight response event and stops
