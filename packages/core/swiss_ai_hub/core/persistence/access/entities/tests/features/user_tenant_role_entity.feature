Feature: User Tenant Role Entity
  As a developer, I want a robust user-tenant-role management system
  So that I can securely assign and manage user roles within tenants.

  Background:
    Given the default tenant exists with access rules "aihub.admin.>"
    And the system role "AIHubUser" exists with access rules "aihub.user.>"
    And the system role "AIHubAdmin" exists with access rules "aihub.admin.>"

  Scenario: Create a new user-tenant-role association
    Given a user "user-123" does not have an association with the default tenant
    When I create an association for user "user-123" with roles "AIHubUser"
    Then user "user-123" should have roles "AIHubUser" in the default tenant

  Scenario: Update an existing user-tenant-role association
    Given a user "user-456" has roles "AIHubUser" in the default tenant
    When I update the association for user "user-456" with roles "AIHubAdmin"
    Then user "user-456" should have roles "AIHubAdmin" in the default tenant

  Scenario: Add roles to an existing association
    Given a user "user-789" has roles "AIHubUser" in the default tenant
    When I add roles "AIHubAdmin" to user "user-789" in the default tenant
    Then user "user-789" should have roles "AIHubUser, AIHubAdmin" in the default tenant

  Scenario: Remove roles from an existing association
    Given a user "user-remove" has roles "AIHubUser, AIHubAdmin" in the default tenant
    When I remove roles "AIHubAdmin" from user "user-remove" in the default tenant
    Then user "user-remove" should have roles "AIHubUser" in the default tenant

  Scenario: Remove user from tenant
    Given a user "user-delete" has roles "AIHubUser" in the default tenant
    When I remove user "user-delete" from the default tenant
    Then user "user-delete" should have no association with the default tenant

  Scenario: Get roles for user with no association
    Given a user "user-no-assoc" does not have an association with the default tenant
    Then user "user-no-assoc" should have no roles in the default tenant

  Scenario: Creating association with invalid roles logs warning and ignores them
    Given a user "user-invalid" does not have an association with the default tenant
    When I create an association for user "user-invalid" with roles "AIHubUser, NonExistentRole"
    Then user "user-invalid" should have roles "AIHubUser" in the default tenant

  Scenario: Adding invalid roles logs warning and ignores them
    Given a user "user-add-invalid" has roles "AIHubUser" in the default tenant
    When I add roles "NonExistentRole" to user "user-add-invalid" in the default tenant
    Then user "user-add-invalid" should have roles "AIHubUser" in the default tenant

  Scenario: Create association with validation disabled accepts any roles
    Given a user "user-no-validate" does not have an association with the default tenant
    When I create an association for user "user-no-validate" with roles "FakeRole" without validation
    Then user "user-no-validate" should have roles "FakeRole" in the default tenant
