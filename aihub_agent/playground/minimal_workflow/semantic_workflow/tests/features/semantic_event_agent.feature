Feature: Simple Agent
  test for SimpleAgent

  Scenario: Test Simple Agent
    Given a SemanticEventAgent runner

    When a the start event is sent

    Then a StartEvent is present
    And a RetrieverEvent is present
    And a RerankerEvent is present
    And a LLMStopEvent is present


