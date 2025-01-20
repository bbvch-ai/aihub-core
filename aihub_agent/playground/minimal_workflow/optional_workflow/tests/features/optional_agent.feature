Feature: Optional Agent
  Test the OptionalAgent with different event outputs

  Scenario: Test Optional Agent with only EventA
    Given an OptionalAgent runner
    When the start event is sent and random is forced to produce only EventA
    Then an EventA event is present
    And no EventB event is present
    And no EventC event is present
    And an EventD event is present
    And a StopEvent is present

  Scenario: Test Optional Agent with EventA and EventB
    Given an OptionalAgent runner
    When the start event is sent and random is forced to produce EventA and EventB
    Then an EventA event is present
    And an EventB event is present
    And an EventC event is present
    And no EventD event is present
    And a StopEvent is present
