Feature: KeycloakAuthHandler

  Scenario: Valid Keycloak token returns authenticated user
    Given a Keycloak configuration with url "http://keycloak:8080" and realm "aihub"
    And a valid Keycloak token is generated with name "Test User", email "testuser@example.com", and sub "test-sub-id"
    When I invoke the KeycloakAuthHandler with the token
    Then the returned user should have name "Test User"
    And the returned user should have email "testuser@example.com"

  Scenario: Token with missing kid is rejected
    Given a Keycloak configuration with url "http://keycloak:8080" and realm "aihub"
    And a Keycloak token without kid in the header
    When I invoke the KeycloakAuthHandler with the token expecting error
    Then I should receive an HTTP error with detail "Invalid token format"

  Scenario: Token with unknown kid is rejected
    Given a Keycloak configuration with url "http://keycloak:8080" and realm "aihub"
    And a valid Keycloak token is generated with name "Unknown Kid", email "unknownkid@example.com", and sub "unknown-kid-sub"
    And the token header kid is changed to "unknown-key-id"
    When I invoke the KeycloakAuthHandler with the token expecting error
    Then I should receive an HTTP error with detail "Token verification failed"

  Scenario: Token with invalid signature is rejected
    Given a Keycloak configuration with url "http://keycloak:8080" and realm "aihub"
    And a valid Keycloak token is generated with name "Invalid Sig", email "invalidsig@example.com", and sub "invalid-sig-sub"
    And the token is re-signed with a different private key
    When I invoke the KeycloakAuthHandler with the token expecting error
    Then I should receive an HTTP error with detail "Token verification failed: Invalid token"

  Scenario: Expired Keycloak token is rejected
    Given a Keycloak configuration with url "http://keycloak:8080" and realm "aihub"
    And an expired Keycloak token is generated with name "Expired User", email "expired@example.com", and sub "expired-sub"
    When I invoke the KeycloakAuthHandler with the token expecting error
    Then I should receive an HTTP error with detail "Token expired"

  Scenario: Token with issuer mismatch is rejected
    Given a Keycloak configuration with url "http://keycloak:8080" and realm "aihub"
    And a Keycloak token with wrong issuer "https://wrong-issuer/realms/aihub"
    When I invoke the KeycloakAuthHandler with the token expecting error
    Then I should receive an HTTP error with detail "Token verification failed: Invalid token"

  Scenario: Token with audience mismatch is rejected
    Given a Keycloak configuration with url "http://keycloak:8080" and realm "aihub"
    And a Keycloak token with wrong audience "wrong-audience"
    When I invoke the KeycloakAuthHandler with the token expecting error
    Then I should receive an HTTP error with detail "Token verification failed: Invalid token"

  Scenario: JWKS fetch failure returns service unavailable
    Given a Keycloak configuration with url "http://keycloak:8080" and realm "aihub"
    And a valid Keycloak token is generated with name "Test User", email "testuser@example.com", and sub "test-sub-id"
    And the JWKS endpoint is unavailable
    When I invoke the KeycloakAuthHandler with the token expecting error
    Then I should receive an HTTP error with detail "Authentication service unavailable"

  Scenario: Invalid token format is rejected
    Given a Keycloak configuration with url "http://keycloak:8080" and realm "aihub"
    And an invalid Keycloak token "not_a_jwt"
    When I invoke the KeycloakAuthHandler with the token expecting error
    Then I should receive an HTTP error with detail "Token verification failed: Invalid token"
