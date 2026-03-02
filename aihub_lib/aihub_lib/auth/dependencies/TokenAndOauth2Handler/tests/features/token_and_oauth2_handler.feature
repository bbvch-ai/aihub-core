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

