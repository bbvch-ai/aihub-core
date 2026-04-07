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

  Scenario: Explicit tenant path parameter resolves to specified tenant
    Given a request with tenant path parameter set to the second tenant
    When the auth handler resolves tenant for user "user-1"
    Then the resolved tenant should be "Acme Corp"

  Scenario: Active tenant path parameter without active tenant returns 400 error
    Given a request with tenant path parameter set to "active"
    When the auth handler resolves tenant for user "user-1" expecting error
    Then a 400 error should be raised with message "No active tenant set"

  Scenario: Invalid tenant ID returns 403 error
    Given a request with tenant path parameter set to "non-existent-tenant-id"
    When the auth handler resolves tenant for user "user-1" expecting error
    Then a 403 error should be raised with message "Access denied"

  Scenario: User without tenant membership returns 403 error
    Given a request with tenant path parameter set to the second tenant
    When the auth handler resolves tenant for user "user-2" expecting error
    Then a 403 error should be raised with message "Access denied"

  Scenario: No active tenant set returns 400 error regardless of default tenant
    Given no default tenant exists
    And a request with tenant path parameter set to "active"
    When the auth handler resolves tenant for user "user-1" expecting error
    Then a 400 error should be raised with message "No active tenant set"

  Scenario: Get active tenant for user without active tenant returns 400 error
    When the auth handler gets active tenant for user "user-1" expecting error
    Then a 400 error should be raised with message "No active tenant set"

  Scenario: Get active tenant for user with active tenant set resolves correctly
    Given user "user-1" has active tenant set to the second tenant
    When the auth handler gets active tenant for user "user-1"
    Then the resolved tenant should be "Acme Corp"

  Scenario: Non-existent tenant ID returns generic 403 without leaking information
    Given a request with tenant path parameter set to "000000000000000000000000"
    When the auth handler resolves tenant for user "user-1" expecting error
    Then a 403 error should be raised with message "Access denied"

  Scenario: Superuser virtual tenant ID cannot be used by regular users
    Given a request with tenant path parameter set to "__superuser_tenant__"
    When the auth handler resolves tenant for user "user-1" expecting error
    Then a 403 error should be raised with message "Access denied"

  Scenario: Active tenant is used when path parameter is active
    Given user "user-1" has active tenant set to the second tenant
    And a request with tenant path parameter set to "active"
    When the auth handler resolves tenant for user "user-1"
    Then the resolved tenant should be "Acme Corp"

  Scenario: Explicit tenant path parameter does not update active tenant
    Given user "user-1" has active tenant set to the default tenant
    And a request with tenant path parameter set to the second tenant
    When the auth handler resolves tenant for user "user-1"
    Then the resolved tenant should be "Acme Corp"
    And user "user-1" should have active tenant set to the default tenant

  Scenario: Stale active tenant returns 400 error
    Given user "user-1" has active tenant set to "000000000000000000000000"
    And a request with tenant path parameter set to "active"
    When the auth handler resolves tenant for user "user-1" expecting error
    Then a 400 error should be raised with message "Your active tenant is no longer accessible"

  Scenario: Active tenant without membership returns 400 error
    Given user "user-2" has active tenant set to the second tenant
    And a request with tenant path parameter set to "active"
    When the auth handler resolves tenant for user "user-2" expecting error
    Then a 400 error should be raised with message "Your active tenant is no longer accessible"

  Scenario: WebSocket context uses active tenant
    Given user "user-1" has active tenant set to the second tenant
    When the auth handler gets active tenant for user "user-1"
    Then the resolved tenant should be "Acme Corp"

  Scenario: WebSocket with stale active tenant returns 400 error
    Given user "user-1" has active tenant set to "000000000000000000000000"
    When the auth handler gets active tenant for user "user-1" expecting error
    Then a 400 error should be raised with message "Your active tenant is no longer accessible"

  Scenario: WebSocket with revoked tenant membership returns 400 error
    Given user "user-2" has active tenant set to the second tenant
    When the auth handler gets active tenant for user "user-2" expecting error
    Then a 400 error should be raised with message "Your active tenant is no longer accessible"
