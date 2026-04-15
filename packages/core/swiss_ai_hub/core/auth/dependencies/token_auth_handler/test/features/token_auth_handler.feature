Feature: TokenAuthHandler

  Scenario: Valid token returns authenticated user
    Given a token exists in the database with user details: name "Token User", email "token@example.com", and roles "user,editor"
    When I invoke the TokenAuthHandler with an Authorization header using the token
    Then the returned user should have name "Token User"
    And the returned user should have preferred_username "token@example.com"
    And the returned user should have oid matching the token's user id
    And the returned user should have roles "user" and "editor"

  Scenario: Token with invalid format is rejected
    Given an invalid token format "not_a_valid_token"
    When I invoke the TokenAuthHandler with an Authorization header using the token expecting error
    Then I should receive an HTTP error with detail "Invalid token format"

  Scenario: Token not found in database is rejected
    Given a token does not exist in the database with token "sk-nonexistenttokenvalue"
    When I invoke the TokenAuthHandler with an Authorization header using the token expecting error
    Then I should receive an HTTP error with detail "Token not found"

  Scenario: A modified token is rejected as not found
    Given a token exists in the database with user details: name "Mismatch User", email "mismatch@example.com", and roles "user,editor"
    And I modify the token to cause a mismatch
    When I invoke the TokenAuthHandler with an Authorization header using the token expecting error
    Then I should receive an HTTP error with detail "Token not found"

  Scenario: Expired token is rejected
    Given a token exists in the database with user details: name "Expired User", email "expired@example.com", and roles "user,editor"
    And I set the token expiry to a past time
    When I invoke the TokenAuthHandler with an Authorization header using the token expecting error
    Then I should receive an HTTP error with detail "Token expired"
