Feature: Displaying Agent
  Test for DisplayingAgent

  Scenario: Test Displaying Agent
    Given a DisplayingAgent runner

    When the start event is sent

    Then a StartEvent is present
    And a ThoughtEvent is present
    And a ChunkEvent is present
    And a StopEvent is present
