Feature: OpenWebuiAuthHandler

  Scenario: Valid token returns authenticated user
    Given a token exists in the database with user details: name "OpenWebUI User", email "openwebui@example.com", and roles "user,editor"
    And a client_id "test-client", and authority_url "https://login.microsoftonline.com/test-tenant"
    When I invoke the OpenWebuiAuthHandler with the required headers and a valid token
    Then the returned user should have name "OpenWebUI User"
    And the returned user should have preferred_username "openwebui@example.com"
    And the returned user should have oid matching the token's user id
    And the returned user should have roles "user" and "editor"

  Scenario: Token with invalid format is rejected
    Given an invalid token format "not_a_valid_token"
    And a client_id "test-client", and authority_url "https://login.microsoftonline.com/test-tenant"
    When I invoke the OpenWebuiAuthHandler with the required headers and a token expecting error
    Then I should receive an HTTP error with detail "Invalid token format"

  Scenario: Token not found in database is rejected
    Given a token does not exist in the database with token "123456789012345678901234.random123"
    And a client_id "test-client", and authority_url "https://login.microsoftonline.com/test-tenant"
    When I invoke the OpenWebuiAuthHandler with the required headers and a token expecting error
    Then I should receive an HTTP error with detail "Token not found"

  Scenario: Token mismatch causes rejection
    Given a token exists in the database with user details: name "Mismatch User", email "mismatch@example.com", and roles "user,editor"
    And a client_id "test-client", and authority_url "https://login.microsoftonline.com/test-tenant"
    And I modify the token to cause a mismatch
    When I invoke the OpenWebuiAuthHandler with the required headers and a token expecting error
    Then I should receive an HTTP error with detail "Token mismatch"

  Scenario: Expired token is rejected
    Given a token exists in the database with user details: name "Expired User", email "expired@example.com", and roles "user,editor"
    And a client_id "test-client", and authority_url "https://login.microsoftonline.com/test-tenant"
    And I set the token expiry to a past time
    When I invoke the OpenWebuiAuthHandler with the required headers and a token expecting error
    Then I should receive an HTTP error with detail "Token expired"
