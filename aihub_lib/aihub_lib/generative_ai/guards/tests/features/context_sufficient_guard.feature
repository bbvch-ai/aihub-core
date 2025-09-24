Feature: Context Sufficient Guard Logic

  Scenario: Guard accepts when context is sufficient to answer question
    Given a locale handler with locale "en"
    And a user query "What is the capital of France?"
    And the following context "France is a country in Europe. Paris is the capital and largest city of France."
    And no previous queries
    And more hops are available
    And the LLM returns success=True with reasoning="The context clearly states Paris is the capital"
    When the context sufficient guard is executed
    Then the guard should accept the request
    And the reasoning should be "The context clearly states Paris is the capital"
    And no new query should be generated

  Scenario: Guard rejects when context is insufficient and generates new query
    Given a locale handler with locale "en"
    And a user query "What is the population of France?"
    And the following context "France is a country in Europe."
    And the following previous queries:
      | query                             |
      | What are European countries?      |
    And more hops are available
    And the LLM returns success=False with reasoning="Context lacks population data" and new_query="Demographics of European countries"
    When the context sufficient guard is executed
    Then the guard should reject the request
    And the reasoning should be "Context lacks population data"
    And a new query "Demographics of European countries" should be generated

  Scenario: Guard rejects when context is insufficient and no more hops available
    Given a locale handler with locale "en"
    And a user query "What is the GDP of France?"
    And the following context "France is a country."
    And no previous queries
    And no more hops are available
    And the LLM returns success=False with reasoning="Insufficient economic data in context"
    When the context sufficient guard is executed
    Then the guard should reject the request
    And the reasoning should be "Insufficient economic data in context"
    And no new query should be generated