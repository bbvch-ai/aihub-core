Feature: TokenAuthHandler

  Scenario: Valid token returns authenticated user
    Given a token exists in the database with user details: name "Token User", email "token@example.com", and roles "user,editor"
    When I invoke the TokenAuthHandler with an Authorization header using the token
    Then the returned user should have name "Token User"
    And the returned user should have preferred_username "token@example.com"
    And the returned user should have oid matching the token's id
    And the returned user should have roles "user" and "editor"
