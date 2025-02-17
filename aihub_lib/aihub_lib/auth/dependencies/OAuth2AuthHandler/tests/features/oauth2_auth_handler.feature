Feature: OAuth2AuthHandler

  Scenario: Valid OAuth2 token returns authenticated user
    Given an OAuth2 configuration with tenant_id "test-tenant", client_id "test-client", and authority_url "https://login.microsoftonline.com"
    And a valid OAuth2 token is generated with name "Test User", email "testuser@example.com", and roles "user,admin"
    When I invoke the OAuth2AuthHandler with the token
    Then the returned user should have name "Test User"
    And the returned user should have preferred_username "testuser@example.com"
    And the returned user should have roles "user" and "admin"
