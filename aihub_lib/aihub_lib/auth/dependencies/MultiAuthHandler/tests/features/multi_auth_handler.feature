Feature: MultiAuthHandler composite authentication

  Scenario: First handler succeeds
    Given a multi auth handler composed of:
      | handler_name     | behavior    | detail      |
      | DummySuccessAuth | success     |             |
      | DummyFailureAuth | failure_401 | Dummy error |
    When I invoke the multi auth handler
    Then the returned user should have name "Dummy Success"

  Scenario: First fails with 401, second succeeds
    Given a multi auth handler composed of:
      | handler_name     | behavior    | detail       |
      | DummyFailureAuth | failure_401 | First error  |
      | DummySuccessAuth | success     |             |
    When I invoke the multi auth handler
    Then the returned user should have name "Dummy Success"

  Scenario: All handlers fail with 401 errors
    Given a multi auth handler composed of:
      | handler_name     | behavior    | detail    |
      | DummyFailureAuth | failure_401 | Error one |
      | DummyFailureAuth | failure_401 | Error two |
    When I invoke the multi auth handler expecting error
    Then I should receive an HTTP error with detail "DummyFailureAuth: Error one | DummyFailureAuth: Error two"

  Scenario: A handler fails with a non-401 error
    Given a multi auth handler composed of:
      | handler_name         | behavior          | detail           |
      | DummyFailureNon401   | failure_non_401   | Critical error   |
      | DummySuccessAuth     | success           |                |
    When I invoke the multi auth handler expecting error
    Then I should receive an HTTP error with detail "Critical error"
