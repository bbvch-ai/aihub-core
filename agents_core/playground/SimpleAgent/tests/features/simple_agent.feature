Feature: Simple Agent
  test for SimpleAgent

  Scenario: Test Simple Agent
    Given an test runner
    When a the start event is sent with payload "Hello"
    Then runner has start event
    And runner has stop event
    And runner has event A with payload "Hell Nah"


