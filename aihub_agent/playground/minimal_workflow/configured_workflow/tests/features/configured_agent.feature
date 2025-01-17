Feature: Configured Agent
  Test for ConfiguredAgent

  Scenario: Test Configured Agent with StartStepConfig and AgentConfig
    Given a ConfiguredAgent runner with agent value "test_agent_value" and step value "test_step_value"

    When the start event is sent
    Then an EventA event is present
    And the agent configuration value "test_agent_value" is processed
    And the step configuration value "test_step_value" is processed
    And a StopEvent is present
