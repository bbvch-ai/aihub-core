Feature: Custom Start Stop Agent
  test for Custom Start Stop Agent

  Scenario: Test Custom Start Stop Agent
    Given a CustomStartStopEventAgent runner

    When a the custom start event is sent with payload "Hello"
    Then a CustomStartEvent is present with payload "Hello"
    And an CustomStopEvent event is present with payload "Hello"


