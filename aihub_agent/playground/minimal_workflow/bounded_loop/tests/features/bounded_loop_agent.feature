Feature: Configured Agent
  test for ConfiguredAgent

  Scenario: Test Configured Agent
    Given a BoundedLoopAgent runner with a loop_max value of "2"

    When a the start event is sent
    Then a StartEvent is present
    Then "3" BeginEvent are present
    Then "3" BoundedLoopAEvent are present
    Then a DecisionEvent is present
    Then a StopEvent is present