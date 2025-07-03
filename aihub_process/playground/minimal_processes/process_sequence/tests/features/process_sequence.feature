Feature: Process Sequence
  Test for InitialProcess triggering SubsequentProcess

  Scenario: Test process sequence workflow
    Given an AgentA runner for sequence
    And an InitialProcess runner
    And a SubsequentProcess runner
    When AgentA is started with payload for process sequence "Sequence Start"
    Then SubsequentProcess produces a CustomProcessStopEvent with payload "Sequence Start -> AgentA processed -> InitialProcess output -> SubsequentProcess output"