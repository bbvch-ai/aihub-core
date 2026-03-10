Feature: Fan Out Process
  Test for FanOutProcess interacting with AgentA and fanning out to AgentB

  Scenario: Test FanOutProcess workflow
    Given an AgentA runner
    And an AgentB runner
    And a FanOutProcess runner
    When AgentA is started with payload for FanOutProcess "FanOut Input"
    Then FanOutProcess produces a CustomProcessStopEvent with payload "FanOut Input -> AgentA processed -> Branch 1 -> AgentB processed | FanOut Input -> AgentA processed -> Branch 2 -> AgentB processed -> FanOutProcess output"