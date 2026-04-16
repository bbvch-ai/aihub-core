Feature: NoAuthHandler

  Scenario: NoAuthHandler returns a static user
    Given a NoAuth configuration with name "Test User", email "test@example.com", oid "12345", and roles "user,admin"
    When I invoke the DangerousDevelopmentOnlyAuthHandler with a dummy request
    Then the returned user should have name "Test User"
    And the returned user should have preferred_username "test@example.com"
    And the returned user should have oid "12345"
    And the returned user should have roles "user" and "admin"
