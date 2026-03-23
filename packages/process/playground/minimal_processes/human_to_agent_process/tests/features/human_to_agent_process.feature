Feature: Human To Agent Process
  Test for HumanToAgentProcess interacting with a Human and AgentA

  Scenario: Test HumanToAgentProcess workflow
    Given a HumanToAgentProcess runner
    And an AgentA runner
    When a human sends work with payload "Human input"
    Then HumanToAgentProcess produces a CustomProcessStopEvent with payload "Human input -> AgentA processed -> HumanToAgentProcess output"