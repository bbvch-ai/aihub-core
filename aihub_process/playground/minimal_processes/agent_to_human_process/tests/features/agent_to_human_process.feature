Feature: Agent To Human Process
  Test for AgentToHumanProcess interacting with AgentA and a Human

  Scenario: Test AgentToHumanProcess workflow
    Given an AgentToHumanProcess runner
    And an AgentA runner
    When AgentA starts the process with payload "Agent initial data" and a human responds with "Human final word"
    Then AgentToHumanProcess produces a CustomProcessStopEvent with payload "Please respond to <Agent initial data -> AgentA processed> with a single word: -> Human final word -> AgentToHumanProcess output"