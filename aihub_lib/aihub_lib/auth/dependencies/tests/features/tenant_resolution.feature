Feature: Tenant Resolution in Auth Handler
  As a developer, I want the auth handler to correctly resolve tenant context
  So that users are properly scoped to their tenants.

  Background:
    Given the default tenant exists with name "Default Org" and access rules "aihub.admin.>"
    And a second tenant exists with name "Acme Corp" and access rules "aihub.user.>"
    And the system role "AIHubUser" exists
    And user "user-1" is a member of the default tenant with roles "AIHubUser"
    And user "user-1" is a member of the second tenant with roles "AIHubUser"
    And user "user-2" is a member of the default tenant only with roles "AIHubUser"

  Scenario: Valid x-tenant-id header resolves to specified tenant
    Given a request with x-tenant-id header set to the second tenant
    When the auth handler resolves tenant for user "user-1"
    Then the resolved tenant should be "Acme Corp"

  Scenario: Missing x-tenant-id header falls back to default tenant
    Given a request without x-tenant-id header
    When the auth handler resolves tenant for user "user-1"
    Then the resolved tenant should be "Default Org"

  Scenario: Invalid tenant ID returns 403 error
    Given a request with x-tenant-id header set to "non-existent-tenant-id"
    When the auth handler resolves tenant for user "user-1" expecting error
    Then a 403 error should be raised with message "Access denied"

  Scenario: User without tenant membership returns 403 error
    Given a request with x-tenant-id header set to the second tenant
    When the auth handler resolves tenant for user "user-2" expecting error
    Then a 403 error should be raised with message "Access denied"

  Scenario: No default tenant and no header returns 500 error
    Given no default tenant exists
    And a request without x-tenant-id header
    When the auth handler resolves tenant for user "user-1" expecting error
    Then a 500 error should be raised with message "No default tenant configured"

  Scenario: Get active tenant for user works without request
    When the auth handler gets active tenant for user "user-1"
    Then the resolved tenant should be "Default Org"

  Scenario: Get active tenant for user without membership returns 403 error
    Given user "user-no-default" is a member of the second tenant only with roles "AIHubUser"
    When the auth handler gets active tenant for user "user-no-default" expecting error
    Then a 403 error should be raised with message "Access denied"

  Scenario: Non-existent tenant ID returns generic 403 without leaking information
    Given a request with x-tenant-id header set to "000000000000000000000000"
    When the auth handler resolves tenant for user "user-1" expecting error
    Then a 403 error should be raised with message "Access denied"

  Scenario: Superuser virtual tenant ID cannot be used by regular users
    Given a request with x-tenant-id header set to "__superuser_tenant__"
    When the auth handler resolves tenant for user "user-1" expecting error
    Then a 403 error should be raised with message "Access denied"

  Scenario: Active tenant is used when no header provided
    Given user "user-1" has active tenant set to the second tenant
    And a request without x-tenant-id header
    When the auth handler resolves tenant for user "user-1"
    Then the resolved tenant should be "Acme Corp"

  Scenario: Explicit header updates active tenant
    Given user "user-1" has active tenant set to the default tenant
    And a request with x-tenant-id header set to the second tenant
    When the auth handler resolves tenant for user "user-1"
    Then the resolved tenant should be "Acme Corp"
    And user "user-1" should have active tenant set to the second tenant

  Scenario: Stale active tenant falls back to default
    Given user "user-1" has active tenant set to "000000000000000000000000"
    And a request without x-tenant-id header
    When the auth handler resolves tenant for user "user-1"
    Then the resolved tenant should be "Default Org"
    And user "user-1" should have active tenant set to the default tenant

  Scenario: Active tenant without membership falls back to default
    Given user "user-2" has active tenant set to the second tenant
    And a request without x-tenant-id header
    When the auth handler resolves tenant for user "user-2"
    Then the resolved tenant should be "Default Org"
    And user "user-2" should have active tenant set to the default tenant

  Scenario: WebSocket context uses active tenant
    Given user "user-1" has active tenant set to the second tenant
    When the auth handler gets active tenant for user "user-1"
    Then the resolved tenant should be "Acme Corp"
