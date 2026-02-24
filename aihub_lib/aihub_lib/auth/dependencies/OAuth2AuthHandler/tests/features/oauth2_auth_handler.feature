Feature: OAuth2AuthHandler

  Scenario: Valid OAuth2 token returns authenticated user
    Given an OAuth2 configuration client_id "test-client", and authority_url "https://login.microsoftonline.com/test-tenant"
    And a valid OAuth2 token is generated with name "Test User", email "testuser@example.com", and roles "user,admin"
    And no modification is applied to the token
    When I invoke the OAuth2AuthHandler with the token
    Then the returned user should have name "Test User"
    And the returned user should have preferred_username "testuser@example.com"

  Scenario: Invalid token format is rejected
    Given an OAuth2 configuration client_id "test-client", and authority_url "https://login.microsoftonline.com/test-tenant"
    And an invalid OAuth2 token "not_a_jwt"
    When I invoke the OAuth2AuthHandler with the token expecting error
    Then I should receive an HTTP error with detail "Token verification failed: Invalid token"

  Scenario: Expired OAuth2 token is rejected
    Given an OAuth2 configuration client_id "test-client", and authority_url "https://login.microsoftonline.com/test-tenant"
    And an expired OAuth2 token is generated with name "Expired User", email "expired@example.com", and roles "user"
    When I invoke the OAuth2AuthHandler with the token expecting error
    Then I should receive an HTTP error with detail "Token verification failed"

  Scenario: Token with unknown key id is rejected
    Given an OAuth2 configuration client_id "test-client", and authority_url "https://login.microsoftonline.com/test-tenant"
    And a valid OAuth2 token is generated with name "Unknown Kid", email "unknownkid@example.com", and roles "user,admin"
    And I modify the token's header to use kid "unknown-key-id"
    When I invoke the OAuth2AuthHandler with the token expecting error
    Then I should receive an HTTP error with detail "Token verification failed"

  Scenario: Token with invalid signature is rejected
    Given an OAuth2 configuration client_id "test-client", and authority_url "https://login.microsoftonline.com/test-tenant"
    And a valid OAuth2 token is generated with name "Invalid Signature", email "invalidsig@example.com", and roles "user"
    And I re-sign the token with a different private key
    When I invoke the OAuth2AuthHandler with the token expecting error
    Then I should receive an HTTP error with detail "Token verification failed: Invalid token"
