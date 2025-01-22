Feature: Displaying Agent
  Test for DisplayingAgent

  Scenario: Test Displaying Agent
    Given a DisplayingAgent runner

    When the start event is sent

    Then a StartEvent is present
    And a ThoughtEvent with content "Let me think...." is present
    And a ChunkEvent with content "This is some chunk that is sent to the user" is present
    And a StopEvent is present
