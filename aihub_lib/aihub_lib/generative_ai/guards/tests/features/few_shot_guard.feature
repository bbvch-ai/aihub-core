Feature: Few-Shot Guard Validation

  Scenario: Validate few-shot guard with valid inputs
    Given a locale handler with locale "en"
    And the following few-shot examples:
      | user_message         | success | reason             |
      | Example user query 1 | True    | Valid query        |
      | Example user query 2 | False   | Out of scope query |
    And a user query "Test user query"
    When the few-shot guard is executed
    Then structured_predict should be called
    And structured_predict should be called with prompt:
      """
      You will be provided with a series of example user messages, each labeled with a success status and an explanation.
      These examples define the types of queries the agent is allowed to answer.
      - If a query is allowed, the success status is **true**.
      - If a query is not allowed, the success status is **false**, along with a justification.
      Your task is to determine whether a new user query is permissible based on these examples.
      **Examples:**
      <Examples>
      <User>
      Example user query 1
      </User>
      <Success>
      True
      </Success>
      <Reason>
      Valid query
      </Reason>
      <User>
      Example user query 2
      </User>
      <Success>
      False
      </Success>
      <Reason>
      Out of scope query
      </Reason>
      </Examples>
      **User Query:**
      <UserQuery>
      Test user query
      </UserQuery>
      """
