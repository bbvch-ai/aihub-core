Feature: Context Agent
  test for ContextAgent

  Scenario: The agent starts with a single run context in a thread
    Given a ContextAgent is started with the payload "InitialRun"

    When the agent successfully started
    And the thread context count is "1"
    And the run context count is "1"

    Then a ContextEvent is returned with thread count "1" and run count "1"

  Scenario: The agent starts a second run context in the same thread
    Given another ContextAgent is started with the payload "SecondRun"

    When the agent successfully started
    And the thread context count is "1"

    Then a ContextEvent is returned with thread count "2" and run count "1"

  Scenario: The agent has 2 runs in the same thread
    Given another ContextAgent is started with the payload "SecondRun"

    When the agent successfully started
    And the thread context count is "2"

    Then the agent stopped

