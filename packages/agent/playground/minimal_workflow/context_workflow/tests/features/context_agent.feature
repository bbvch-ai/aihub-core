Feature: Context Agent with Thread and Run Contexts

  Scenario: Multiple runs in the same thread with distinct RunContexts
    Given a ContextAgent test runner

    When two start events are sent with payload "Run 1" and "Run 2" for the same thread

    Then the thread context count should increment to either '1' or '2'
    And each RunContext count should be '1'