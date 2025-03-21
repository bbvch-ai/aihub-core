Feature: Custom Start Stop Agent
  test for Custom Start Stop Agent

  Scenario: Test Custom Start Stop Agent
    Given a CustomStartStopEventAgent runner

    When a the custom start event is sent with payload "Hello"
    Then a MyCustomStartEvent is present with payload "Hello"
    And an MyCustomStopEvent event is present with payload "Hello"


