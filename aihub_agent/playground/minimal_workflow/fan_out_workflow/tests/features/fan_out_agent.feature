Feature: Fan Out Agent
  Test for FanOutAgent

  Scenario: Test FanOutAgent fan-out workflow
    Given a FanOutAgent runner
    When the start event is sent
    Then 5 EventA events with payloads "0,1,2,3,4" are present
    And 5 EventB events with matching payloads "0,1,2,3,4" are present
    And a StopEvent is present
