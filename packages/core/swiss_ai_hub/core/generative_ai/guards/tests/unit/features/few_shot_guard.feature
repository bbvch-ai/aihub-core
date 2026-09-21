Feature: Few-Shot Guard

  The guard asks the model for a plain-text ALLOW/BLOCK verdict (reasoning models cannot reliably
  produce structured output) and parses it. On an unrecognizable response it fails open (accepts).

  Scenario: Accepts a request matching an allowed example
    Given a locale handler with locale "en"
    And the following few-shot examples:
      | user_message       | success | reason        |
      | Reset my password  | True    | IT support    |
      | Write me a poem    | False   | Off topic     |
    And a user query "My laptop will not connect to the VPN"
    And the guard model replies "ALLOW Matches the IT support example"
    When the few-shot guard is executed
    Then the guard should accept the request
    And the reasoning should be "Matches the IT support example"

  Scenario: Rejects a request matching a disallowed example
    Given a locale handler with locale "en"
    And the following few-shot examples:
      | user_message       | success | reason        |
      | Reset my password  | True    | IT support    |
      | Write me a poem    | False   | Off topic     |
    And a user query "Tell me a joke"
    And the guard model replies "BLOCK Off topic like the poem example"
    When the few-shot guard is executed
    Then the guard should reject the request
    And the reasoning should be "Off topic like the poem example"

  Scenario: Accepts (fail-open) when the model returns no recognizable verdict
    Given a locale handler with locale "en"
    And the following few-shot examples:
      | user_message       | success | reason        |
      | Reset my password  | True    | IT support    |
    And a user query "My laptop will not connect to the VPN"
    And the guard model replies "Unclear, I cannot decide."
    When the few-shot guard is executed
    Then the guard should accept the request
