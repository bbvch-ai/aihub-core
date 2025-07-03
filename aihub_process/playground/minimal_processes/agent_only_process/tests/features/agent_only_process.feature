Feature: Agent Only Process
  Test for AgentOnlyProcess interacting with AgentA and AgentB

  Scenario: Test AgentOnlyProcess workflow
    Given an AgentA runner
    And an AgentB runner
    And an AgentOnlyProcess runner
    When AgentA is started with payload "Initial Data"
    Then AgentOnlyProcess produces a CustomProcessStopEvent with payload "Initial Data -> AgentA processed -> AgentB processed -> AgentOnlyProcess output"