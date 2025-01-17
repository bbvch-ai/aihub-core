Feature: Fan Out Agent
  Test for FanOutAgent

  Scenario: Test FanOutAgent fan-out workflow
    Given a FanOutAgent runner
    When the start event is sent
    Then 5 EventA events are present
    And 5 EventB events are present
    And a StopEvent is present
