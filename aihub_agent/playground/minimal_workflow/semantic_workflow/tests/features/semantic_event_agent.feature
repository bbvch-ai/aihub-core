Feature: Semantic Event Agent
  test for SemanticEventAgent

  Scenario: Test Semantic Event Agent
    Given a SemanticEventAgent runner

    When a the start event is sent

    Then a StartEvent is present
    And a RetrieverEvent is present that retrieved "3" nodes
    And a RerankerEvent is present
    And a LLMStopEvent is present


