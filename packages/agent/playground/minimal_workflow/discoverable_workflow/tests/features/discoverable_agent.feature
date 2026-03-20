Feature: Discoverable Agent
  test for Discoverable Agent

  Scenario: Test Discoverable Agent
    Given a DiscoverableAgent runner

    When a DiscoveryRequestEvent is sent
    Then a DiscoveryRequestEvent is present
    Then an AgentDiscoveryResponseEvent with the agent's class and ID is present


