Feature: Conditional Agent
  Validates the behavior of the ConditionalAgent, ensuring it processes inputs conditionally and completes the workflow.

  Scenario: Process input with a random value greater than 0.5
    Given a ConditionalAgent runner
    When the start event is sent and the random value is 0.6
    Then the agent processes the branch for values greater than 0.5
    And the workflow completes successfully

  Scenario: Process input with a random value less than or equal to 0.5
    Given a ConditionalAgent runner
    When the start event is sent and the random value is 0.4
    Then the agent processes the branch for values less than or equal to 0.5
    And the workflow completes successfully

