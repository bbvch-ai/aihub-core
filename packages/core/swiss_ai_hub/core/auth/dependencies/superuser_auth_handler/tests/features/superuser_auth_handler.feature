Feature: SuperuserAuthHandler
  The SuperuserAuthHandler provides authentication for a global superuser with full access.

  Scenario: Successful authentication with valid superuser token
    Given a superuser configuration with name "Super Admin", email "admin@example.com", oid "admin-123", role "AIHubSuperuser", and token "secret-token-4f517978885a2bd7b8065be4d16cc422c6d7c37292db9fbc7da23eabc8d35585"
    When I authenticate with token "secret-token-4f517978885a2bd7b8065be4d16cc422c6d7c37292db9fbc7da23eabc8d35585"
    Then the returned user should have name "Super Admin"
    And the returned user should have email "admin@example.com"
    And the returned user should have oid "admin-123"
    And the returned user should have role "AIHubSuperuser"

  Scenario: Failed authentication with invalid token
    Given a superuser configuration with name "Super Admin", email "admin@example.com", oid "admin-123", role "AIHubSuperuser", and token "secret-token-4f517978885a2bd7b8065be4d16cc422c6d7c37292db9fbc7da23eabc8d35585"
    When I authenticate with token "wrong-token"
    Then an HTTPException with status code 401 should be raised
    And the exception detail should be "Invalid token."

  Scenario: Failed authentication with empty token
    Given a superuser configuration with name "Super Admin", email "admin@example.com", oid "admin-123", role "AIHubSuperuser", and token "secret-token-4f517978885a2bd7b8065be4d16cc422c6d7c37292db9fbc7da23eabc8d35585"
    When I authenticate with an empty token
    Then an HTTPException with status code 401 should be raised
    And the exception detail should be "Token missing."

  Scenario: Authentication with custom role configuration
    Given a superuser configuration with name "Custom Admin", email "custom@example.com", oid "custom-456", role "CustomSuperuser", and token "custom-token-d06d685aa26235acf69cd841fae377eaebbe2aaad17c4b73bab92aa77be0e256"
    When I authenticate with token "custom-token-d06d685aa26235acf69cd841fae377eaebbe2aaad17c4b73bab92aa77be0e256"
    Then the returned user should have name "Custom Admin"
    And the returned user should have email "custom@example.com"
    And the returned user should have oid "custom-456"
    And the returned user should have role "CustomSuperuser"