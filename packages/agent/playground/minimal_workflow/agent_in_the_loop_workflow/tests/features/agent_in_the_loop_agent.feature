Feature: Agent In The Loop Workflow
  Test for OrchestratorAgent and WorkerAgent interaction

  Scenario: Test Orchestrator successfully delegates work to Worker Agent
    Given an OrchestratorAgent runner
    And a WorkerAgent runner
    When a start event with message "8" is sent to the orchestrator
    Then a StartEvent is received by the orchestrator
    And an AgentInTheLoopRequest is received by the orchestrator
    And an AgentInTheLoopResponse with result 16 is received by the orchestrator
    And an OrchestrationResultEvent with result 16 is received by the orchestrator

  Scenario: Test Orchestrator delegates work but worker fails
    Given an OrchestratorAgent runner
    And a WorkerAgent runner
    When a start event with message "not-a-number" is sent to the orchestrator
    Then a StartEvent is received by the orchestrator
    And an AgentInTheLoopRequest is received by the orchestrator
    And an AgentInTheLoopResponse with exception is received by the orchestrator
    And an OrchestrationResultEvent with result -1 is received by the orchestrator

  Scenario: Test AITL response is not duplicated
    Given an OrchestratorAgent runner
    And a WorkerAgent runner
    When a start event with message "8" is sent to the orchestrator
    Then exactly 1 unique AgentInTheLoopResponse is received by the orchestrator
    And exactly 1 unique OrchestrationResultEvent is received by the orchestrator

  Scenario: Test Orchestrator handles unknown Worker events
    Given an OrchestratorAgent runner
    And a WorkerAgent runner
    And WorkerStopEvent is removed from the registry
    When a start event with message "8" is sent to the orchestrator
    Then a StartEvent is received by the orchestrator
    And an AgentInTheLoopRequest is received by the orchestrator
    And an AgentInTheLoopResponse with unknown event type is received by the orchestrator
    And an OrchestrationResultEvent with result 16 is received by the orchestrator
    And WorkerStopEvent is restored to the registry