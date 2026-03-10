Feature: Multi-Tenant Access Control Integration
  As a developer, I want to verify that the access control system correctly handles
  multi-tenant scenarios where users have different roles across different tenants.

  Background:
    Given tenant "Alpha Corp" exists with access rules "aihub.admin.>"
    And tenant "Beta Inc" exists with access rules "aihub.user.agent.>"
    And the system role "AIHubAdmin" exists with access rules "aihub.admin.>"
    And the system role "AIHubUser" exists with access rules "aihub.user.>"

  Scenario: User with admin in one tenant and user in another gets correct access levels
    Given user "multi-tenant-user" has role "AIHubAdmin" in tenant "Alpha Corp"
    And user "multi-tenant-user" has role "AIHubUser" in tenant "Beta Inc"
    When checking access for user "multi-tenant-user" in tenant "Alpha Corp" to "aihub.user.agent.class-a.id-1"
    Then the access level should be ACCESS_ADMIN
    When checking access for user "multi-tenant-user" in tenant "Beta Inc" to "aihub.user.agent.class-a.id-1"
    Then the access level should be ACCESS_USER

  Scenario: Tenant access rules cap user permissions
    Given user "capped-user" has role "AIHubAdmin" in tenant "Beta Inc"
    When checking access for user "capped-user" in tenant "Beta Inc" to "aihub.user.agent.class-a.id-1"
    Then the access level should be ACCESS_USER
    When checking access for user "capped-user" in tenant "Beta Inc" to "aihub.user.process.class-a.id-1"
    Then the access level should be ACCESS_DENIED

  Scenario: User gets denied for resource outside tenant's access rules
    Given user "limited-user" has role "AIHubUser" in tenant "Beta Inc"
    When checking access for user "limited-user" in tenant "Beta Inc" to "aihub.user.process.class-a.id-1"
    Then the access level should be ACCESS_DENIED

  Scenario: Same user has different implicit access across tenants
    Given user "implicit-user" has role "AIHubUser" in tenant "Alpha Corp"
    And user "implicit-user" has role "AIHubUser" in tenant "Beta Inc"
    When checking access for user "implicit-user" in tenant "Alpha Corp" to "aihub.user.process.?>"
    Then the access level should be ACCESS_USER
    When checking access for user "implicit-user" in tenant "Beta Inc" to "aihub.user.process.?>"
    Then the access level should be ACCESS_DENIED
