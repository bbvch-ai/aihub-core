Feature: MultiAuthHandler composite authentication

  Scenario: First handler succeeds
    Given a Keycloak configuration with url "http://keycloak:8080" and realm "test-realm"
    And a multi auth handler composed of:
      | handler_name     | behavior    | detail      |
      | DummySuccessAuth | success     |             |
      | DummyFailureAuth | failure_401 | Dummy error |
    When I invoke the multi auth handler
    Then the returned user should have name "Dummy Success"

  Scenario: First fails with 401, second succeeds
    Given a Keycloak configuration with url "http://keycloak:8080" and realm "test-realm"
    And a multi auth handler composed of:
      | handler_name     | behavior    | detail       |
      | DummyFailureAuth | failure_401 | First error  |
      | DummySuccessAuth | success     |             |
    When I invoke the multi auth handler
    Then the returned user should have name "Dummy Success"

  Scenario: A handler that accepts the credentials but denies tenant access answers with its 403
    Given a Keycloak configuration with url "http://keycloak:8080" and realm "test-realm"
    And a multi auth handler composed of:
      | handler_name     | behavior    | detail         |
      | DummyFailureAuth | failure_401 | Malformed token |
      | DummyFailureAuth | failure_403 | Access denied  |
    When I invoke the multi auth handler expecting a rejection
    Then the rejection should have status 403
    And the rejection detail should be "Access denied"

  Scenario: Failures without a tenant-access denial still combine into one 401
    Given a Keycloak configuration with url "http://keycloak:8080" and realm "test-realm"
    And a multi auth handler composed of:
      | handler_name       | behavior        | detail          |
      | DummyFailureAuth   | failure_401     | Malformed token |
      | DummyFailureNon401 | failure_non_401 | Keycloak down   |
    When I invoke the multi auth handler expecting a rejection
    Then the rejection should have status 401
    And the rejection detail should mention "Malformed token"
    And the rejection detail should mention "Keycloak down"
