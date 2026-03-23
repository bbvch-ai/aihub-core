Feature: Multi Input Process
  Test for MultiInputProcess interacting with AgentA, AgentB, and AgentC

  Scenario: Test MultiInputProcess workflow
    Given an AgentA runner
    And an AgentB runner
    And an AgentC runner
    And a MultiInputProcess runner
    When AgentA is started with payload for MultiInputProcess "Multi Input"
    Then MultiInputProcess produces a CustomProcessStopEvent with payload "Multi Input -> AgentA processed -> AgentB processed | Multi Input -> AgentA processed -> AgentC processed -> MultiInputProcess output"