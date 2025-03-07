Feature: Precondition Agent
  Test for PreconditionAgent

  Scenario: Test PreconditionAgent workflow
    Given a PreconditionAgent runner with 5 events
    When the start event is sent
    Then 5 ParallelEvent events with payloads "0,1,2,3,4" are present
    And a StopEvent is present
