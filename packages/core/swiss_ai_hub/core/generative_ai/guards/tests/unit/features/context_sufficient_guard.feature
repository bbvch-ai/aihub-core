Feature: Context Sufficient Guard

  The guard asks the model for a plain-text SUFFICIENT/INSUFFICIENT verdict (plus a revised QUERY when
  insufficient and more hops are available) and parses it. A hop needs a query, so an INSUFFICIENT
  verdict with no query is treated as sufficient. An unrecognizable response fails open (sufficient).

  Scenario: Accepts when context is sufficient
    Given a locale handler with locale "en"
    And a user query "How many vacation days do I get?"
    And the following context "Policy: employees receive 25 vacation days per year."
    And no previous queries
    And more hops are available
    And the guard model replies "SUFFICIENT The policy states 25 days"
    When the context sufficient guard is executed
    Then the guard should accept the request
    And the reasoning should be "The policy states 25 days"
    And no new query should be generated

  Scenario: Rejects and generates a new query when insufficient and hops remain
    Given a locale handler with locale "en"
    And a user query "What is the population of France?"
    And the following context "France is a country in Europe."
    And the following previous queries:
      | query                        |
      | What are European countries? |
    And more hops are available
    And the guard model replies "INSUFFICIENT Missing population data QUERY: demographics of European countries"
    When the context sufficient guard is executed
    Then the guard should reject the request
    And the reasoning should be "Missing population data"
    And a new query "demographics of European countries" should be generated

  Scenario: Rejects without a new query when no more hops are available
    Given a locale handler with locale "en"
    And a user query "What is the GDP of France?"
    And the following context "France is a country."
    And no previous queries
    And no more hops are available
    And the guard model replies "INSUFFICIENT No economic data in context"
    When the context sufficient guard is executed
    Then the guard should reject the request
    And the reasoning should be "No economic data in context"
    And no new query should be generated

  Scenario: Accepts when insufficient but the model gives no query and hops remain
    Given a locale handler with locale "en"
    And a user query "What is the population of France?"
    And the following context "France is a country in Europe."
    And no previous queries
    And more hops are available
    And the guard model replies "INSUFFICIENT Not enough detail to answer"
    When the context sufficient guard is executed
    Then the guard should accept the request
    And no new query should be generated

  Scenario: Accepts (fail-open) when the model returns no recognizable verdict
    Given a locale handler with locale "en"
    And a user query "What is the capital of France?"
    And the following context "France is a country in Europe."
    And no previous queries
    And more hops are available
    And the guard model replies "I cannot determine that right now."
    When the context sufficient guard is executed
    Then the guard should accept the request

  Scenario: Forwards chat history into the prompt
    Given a locale handler with locale "en"
    And a user query "What is our vacation policy?"
    And the following context "Employee handbook chapter 3."
    And no previous queries
    And more hops are available
    And the following chat history:
      | role   | content                                |
      | system | [Org memory] Vacation policy: 25 days. |
      | user   | What is our vacation policy?           |
    And the guard model replies "SUFFICIENT Organization memory already answers this"
    When the context sufficient guard is executed with chat history
    Then the guard should accept the request
    And the prompt should include the chat history
