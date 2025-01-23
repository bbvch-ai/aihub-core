Feature: Multistep Human in the Loop Agent
  test for MultistepHumanInTheLoopAgent

  Scenario: The Agent is started and initiates the first HITL-step
    Given a MultistepHumanInTheLoopAgent is started

    When the agent successfully started
    Then the agent initiated the first HITL-step with the question "Shall I continue?"

  Scenario: The first HITL-step is answered with "No, thanks!"
    Given a MultistepHumanInTheLoopAgent is started

    When the agent successfully started
    And the first HITL-step is answered with "No, thanks!"
    Then the agent initiated the second HITL-step with the question "Are you sure?"

  Scenario: The second HITL-step is answered with "Yes, I am sure!"
    Given a MultistepHumanInTheLoopAgent is started

    When the agent successfully started
    And the first HITL-step is answered with "No, thanks!"
    And the second HITL-step is answered with "Yes, I am sure!"
    Then the agent stopped

