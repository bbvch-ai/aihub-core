Feature: OrganizationMemoryAgent - Organization Memory Management
  As a user
  I want to store and retrieve organizational facts
  So that knowledge is shared across all users in my organization

  Background:
    Given an OrganizationMemoryAgent runner with valid configuration

  Scenario: Store new organizational fact and retrieve context
    Given no pre-seeded organization memories
    When the start event is sent with organizational fact "Our company uses Python and Django for backend development"
    Then a StoreOrganizationMemoryEvent is present with memory updates
    And the stored memory contains "Python" and "Django"
    And a RetrieveMemoryEvent is present
    And an AddMemoryToChatHistoryEvent is present
    And an LLMEvent is present
    And the LLM response acknowledges the organizational fact
    And a StopEvent is present

  Scenario: Retrieve existing organizational memories
    Given pre-seeded organization memory: "Our company follows agile methodology with 2-week sprints"
    When the start event is sent with organizational fact "We use JIRA for project management"
    Then a StoreOrganizationMemoryEvent is present
    And a RetrieveMemoryEvent is present with 1 or more memories
    And the retrieved memories contain "agile"
    And an AddMemoryToChatHistoryEvent is present
    And the extended history has a system message with memory context
    And an LLMEvent is present
    And a StopEvent is present

  Scenario: Organization namespace scoping
    Given organization namespace is "Engineering"
    And pre-seeded organization memory in "Engineering" namespace: "We use Python for backend"
    And pre-seeded organization memory in "Marketing" namespace: "We use HubSpot for campaigns"
    When the start event is sent with organizational fact "We deploy on AWS EKS"
    Then a RetrieveMemoryEvent is present
    And the retrieved memories contain "Python" from Engineering namespace
    And the retrieved memories do NOT contain "HubSpot" from Marketing namespace
