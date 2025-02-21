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
      You will receive several examples showing which user requests are allowed and which are not. Each sample response consists of two keys:
      "success": a Boolean (true or false) indicating whether the request is allowed.
      "reasoning": a string containing the reasoning for this decision.
      Important:
      Your final output must be exclusively a JSON object with exactly the two keys “success” and “reasoning”. Do not repeat the entire JSON schema or add additional meta information.
      Your task is to determine whether a new user request is allowed based on these examples.
      **Examples:**
      <Examples>
      <User>
      Example user query 1
      </User>
      <Agent>
      ```{ "success": True,
      "reasoning": "Valid query" }```
      </Agent>
      <User>
      Example user query 2
      </User>
      <Agent>
      ```{ "success": False,
      "reasoning": "Out of scope query" }```
      </Agent>
      </Examples>
      **User Query:**
      <UserQuery>
      Test user query
      </UserQuery>
      """