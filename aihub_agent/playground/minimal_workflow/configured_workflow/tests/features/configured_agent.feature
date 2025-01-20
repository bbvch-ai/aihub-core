Feature: Configured Agent
  test for ConfiguredAgent

  Scenario: Test Configured Agent
    Given a ConfiguredAgent runner with a start step value "Step Config" and an agent value "Agent Config"

    When a the start event is sent
    Then a StartEvent is present
    Then an EventA event is present with payload "Step Config"
    Then an EventB event is present with payload "Agent Config"
    Then a StopEvent is present