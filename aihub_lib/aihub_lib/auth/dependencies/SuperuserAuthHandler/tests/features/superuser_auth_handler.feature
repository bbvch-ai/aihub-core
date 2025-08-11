Feature: SuperuserAuthHandler
  The SuperuserAuthHandler provides authentication for a global superuser with full access.

  Scenario: Successful authentication with valid superuser token
    Given a superuser configuration with name "Super Admin", email "admin@example.com", oid "admin-123", role "AIHubSuperuser", and token "secret-token-123"
    When I authenticate with token "secret-token-123"
    Then the returned user should have name "Super Admin"
    And the returned user should have email "admin@example.com"
    And the returned user should have oid "admin-123"
    And the returned user should have role "AIHubSuperuser"

  Scenario: Failed authentication with invalid token
    Given a superuser configuration with name "Super Admin", email "admin@example.com", oid "admin-123", role "AIHubSuperuser", and token "secret-token-123"
    When I authenticate with token "wrong-token"
    Then an HTTPException with status code 401 should be raised
    And the exception detail should be "Invalid token."

  Scenario: Failed authentication with empty token
    Given a superuser configuration with name "Super Admin", email "admin@example.com", oid "admin-123", role "AIHubSuperuser", and token "secret-token-123"
    When I authenticate with an empty token
    Then an HTTPException with status code 401 should be raised
    And the exception detail should be "Token missing."

  Scenario: Authentication with custom role configuration
    Given a superuser configuration with name "Custom Admin", email "custom@example.com", oid "custom-456", role "CustomSuperuser", and token "custom-token-456"
    When I authenticate with token "custom-token-456"
    Then the returned user should have name "Custom Admin"
    And the returned user should have email "custom@example.com"
    And the returned user should have oid "custom-456"
    And the returned user should have role "CustomSuperuser"