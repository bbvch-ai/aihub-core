Feature: OrganizationMemoryAgent - Organization Memory Management
  As a user
  I want to store and retrieve organizational facts
  So that knowledge is shared across all users in my organization

  Background:
    Given an OrganizationMemoryAgent runner with valid configuration

  Scenario: Full memory workflow - store, retrieve, extend, respond, stop
    Given no pre-seeded organization memories
    When the start event is sent with organizational fact "Our company uses Python and Django for backend development"
    Then a StoreOrganizationMemoryEvent is present with memory updates
    And the stored memory contains "Python" and "Django"
    And a RetrieveOrganizationMemoryEvent is present
    And an AddMemoryToChatHistoryEvent is present
    And the extended history has a system message with memory context
    And the memory system message is after any existing system messages
    And an LLMEvent is present
    And the LLM response acknowledges the stored fact
    And a StopEvent is present

  Scenario: Retrieve existing organizational memories
    Given pre-seeded organization memory: "Our company follows agile methodology with 2-week sprints"
    When the start event is sent with organizational fact "We use JIRA for project management"
    Then a StoreOrganizationMemoryEvent is present
    And a RetrieveOrganizationMemoryEvent is present with 1 or more memories
    And the memory content contains "agile"
    And an AddMemoryToChatHistoryEvent is present
    And the extended history has a system message with memory context
    And an LLMEvent is present
    And a StopEvent is present

  Scenario: Tenant namespace scoping
    Given tenant namespace is "Engineering"
    And pre-seeded tenant memory in "Engineering" namespace: "We use Python for backend"
    And pre-seeded tenant memory in "Marketing" namespace: "We use HubSpot for campaigns"
    When the start event is sent with organizational fact "We deploy on AWS EKS"
    Then a StoreOrganizationMemoryEvent is present
    And a RetrieveOrganizationMemoryEvent is present
    And the memory content contains "Python" from Engineering namespace
    And the memory content does NOT contain "HubSpot" from Marketing namespace
    And an LLMEvent is present
    And a StopEvent is present

  Scenario: Verify stored memory content
    Given no pre-seeded organization memories
    When the start event is sent with organizational fact "Our tech stack includes PostgreSQL and Redis for data storage"
    Then a StoreOrganizationMemoryEvent is present
    And the new memory contains "PostgreSQL" or "Redis"
    And a RetrieveOrganizationMemoryEvent is present
    And an LLMEvent is present
    And a StopEvent is present
