Feature: Displaying Agent
  Test for DisplayingAgent

  Scenario: Test Displaying Agent
    Given a DisplayingAgent runner
    And a mock displayer
    When the start event is sent
    Then the displayer shows the thought "Let me think...."
    And the displayer shows the chunk "This is some chunk that is sent to the user"
    And a StopEvent is present
