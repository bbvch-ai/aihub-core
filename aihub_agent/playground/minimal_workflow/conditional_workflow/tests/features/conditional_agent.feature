Feature: Conditional Agent
  Test for ConditionalAgent

  Scenario: Test Conditional Agent with EventA
    Given a ConditionalAgent runner
    When the start event is sent and random is forced to produce EventA
    Then an EventA event is present
    And a StopEvent is present

  Scenario: Test Conditional Agent with EventB
    Given a ConditionalAgent runner
    When the start event is sent and random is forced to produce EventB
    Then an EventB event is present
    And a StopEvent is present
