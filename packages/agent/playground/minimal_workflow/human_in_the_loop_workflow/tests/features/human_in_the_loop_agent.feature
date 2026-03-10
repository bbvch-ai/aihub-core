Feature: Human In The Loop Agent
  test for HumanInTheLoopAgent

  Scenario: Test Human In The Loop Agent asks for human input
    Given a HumanInTheLoopAgent runner

    When a start event is sent and a HumanInTheLoopResponseEvent event with the response "continue" is sent
    Then a StartEvent is present
    And a HumanInTheLoopRequestEvent event is present
    And a HumanInTheLoopResponseEvent event with the response "continue" is present
    And a StopEvent is present



