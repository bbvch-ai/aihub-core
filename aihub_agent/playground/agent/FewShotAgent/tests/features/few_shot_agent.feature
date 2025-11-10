Feature: Test the FewShotAgent
  In order to verify that the FewShotAgent processes a user query correctly,
  we run a scenario that sends a user message and observes the produced events.

  Scenario: Validate the FewShotAgent workflow
    Given I have an empty agent config
    Given the agent description is "This agent can transform movie titles into emojis."
    And the few shot system prompt is "Respond with three emojis for the movie."
    And the following few-shot examples:
      | user         | agent     |
      | James Bond   | 🤵🍸🔫    |
      | Harry Potter | 👓⚡️🪄    |
      | Thor         | ⚡️🧔‍♂️🔨 |
    And I create a FewShotAgent runner with the config with valid self hosted configuration
    When the start event is sent with a user query "Fight Club"
    Then a StartEvent is present with payload "Fight Club"
    Then a LimitChatHistoryEvent is present
    Then a RightAgentEvent is present
    Then a FewShotStandaloneQuestionCondenserEvent is present with condensed question
    Then a FewShotEvent is present with few shot context
    Then an LLMEvent is present with a generated response
    Then a StopEvent is present
