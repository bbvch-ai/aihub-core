Feature: Simple Agent
  test for SimpleAgent

  Scenario: Test Simple Agent
    Given a SimpleAgent runner

    When a the start event is sent with payload "Hello"
    Then a StartEvent is present with payload "Hello"
    And a StopEvent is present
    And an EventA event is present with payload "Hello"


