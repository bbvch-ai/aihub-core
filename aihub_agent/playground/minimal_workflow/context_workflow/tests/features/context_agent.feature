Feature: Context Agent with Thread and Run Contexts

  Scenario: Multiple runs in the same thread with distinct RunContexts
    Given a mock thread context
    And a mock run context
    And a ContextAgent test runner

    When '3' runs are executed with distinct RunContexts

    Then the thread context count should increment to '3'
    And each RunContext count should be '1'
    And RunContext values should remain isolated across runs