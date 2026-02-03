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

  Scenario: Invalid tenant ID returns 404 error
    Given a request with x-tenant-id header set to "non-existent-tenant-id"
    When the auth handler resolves tenant for user "user-1" expecting error
    Then a 404 error should be raised with message "Tenant non-existent-tenant-id not found"

  Scenario: User without tenant membership returns 403 error
    Given a request with x-tenant-id header set to the second tenant
    When the auth handler resolves tenant for user "user-2" expecting error
    Then a 403 error should be raised with message "User does not have access to tenant"

  Scenario: No default tenant and no header returns 500 error
    Given no default tenant exists
    And a request without x-tenant-id header
    When the auth handler resolves tenant for user "user-1" expecting error
    Then a 500 error should be raised with message "No default tenant configured"

  Scenario: Get default tenant for user works without request
    When the auth handler gets default tenant for user "user-1"
    Then the resolved tenant should be "Default Org"

  Scenario: Get default tenant for user without membership returns 403 error
    Given user "user-no-default" is a member of the second tenant only with roles "AIHubUser"
    When the auth handler gets default tenant for user "user-no-default" expecting error
    Then a 403 error should be raised with message "User does not have access to default tenant"
