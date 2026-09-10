Feature: Agent Description Guard

  The guard asks the model for a plain-text ALLOW/BLOCK verdict (reasoning models cannot reliably
  produce structured output) and parses it. On an unrecognizable response it fails open (accepts).

  Scenario: Accepts an in-scope question
    Given a locale handler with locale "en"
    And an agent description "An assistant that answers HR policy questions"
    And a user query "How many vacation days do I get?"
    And the guard model replies "ALLOW Within the HR scope"
    When the agent description guard is executed
    Then the guard should accept the request
    And the reasoning should be "Within the HR scope"

  Scenario: Blocks an out-of-scope question
    Given a locale handler with locale "en"
    And an agent description "An assistant that answers HR policy questions"
    And a user query "What is the capital of France?"
    And the guard model replies "BLOCK Unrelated to HR"
    When the agent description guard is executed
    Then the guard should reject the request
    And the reasoning should be "Unrelated to HR"

  Scenario: Accepts (fail-open) when the model returns no recognizable verdict
    Given a locale handler with locale "en"
    And an agent description "An assistant that answers HR policy questions"
    And a user query "How many vacation days do I get?"
    And the guard model replies "I am unable to decide right now."
    When the agent description guard is executed
    Then the guard should accept the request
