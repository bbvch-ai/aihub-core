Feature: MultiAuthHandler composite authentication

  Scenario: First handler succeeds
    Given an OAuth2 configuration with tenant_id "test-tenant", client_id "test-client", and authority_url "https://login.microsoftonline.com"
    And a multi auth handler composed of:
      | handler_name     | behavior    | detail      |
      | DummySuccessAuth | success     |             |
      | DummyFailureAuth | failure_401 | Dummy error |
    When I invoke the multi auth handler
    Then the returned user should have name "Dummy Success"

  Scenario: First fails with 401, second succeeds
    Given an OAuth2 configuration with tenant_id "test-tenant", client_id "test-client", and authority_url "https://login.microsoftonline.com"
    And a multi auth handler composed of:
      | handler_name     | behavior    | detail       |
      | DummyFailureAuth | failure_401 | First error  |
      | DummySuccessAuth | success     |             |
    When I invoke the multi auth handler
    Then the returned user should have name "Dummy Success"

