Feature: Sensitive Information Guard Logic

  Scenario: Guard accepts safe response without sensitive information
    Given a locale handler with locale "en"
    And a response "The weather today is sunny and pleasant with temperatures around 22°C."
    And the LLM returns success=True with reasoning="No sensitive information detected - only general weather information"
    When the sensitive info guard is executed
    Then the guard should accept the response
    And the reasoning should be "No sensitive information detected - only general weather information"
    And no cleaned answer should be provided

  Scenario: Guard rejects response containing employee information
    Given a locale handler with locale "en"
    And a response "Please contact John Smith at john.smith@company.com or call his direct line 555-1234 for more details."
    And the LLM returns success=False with reasoning="Contains employee email and phone number" and cleaned_answer="Please contact our customer service team for more details."
    When the sensitive info guard is executed
    Then the guard should reject the response
    And the reasoning should be "Contains employee email and phone number"
    And a cleaned answer "Please contact our customer service team for more details." should be provided

  Scenario: Guard rejects response containing financial data
    Given a locale handler with locale "en"
    And a response "Our Q4 budget shows $2.5M allocated for marketing with a 30% markup on all products."
    And the LLM returns success=False with reasoning="Contains confidential budget and pricing information" and cleaned_answer="Please contact sales for current pricing information."
    When the sensitive info guard is executed
    Then the guard should reject the response
    And the reasoning should be "Contains confidential budget and pricing information"
    And a cleaned answer "Please contact sales for current pricing information." should be provided

  Scenario: Guard rejects response containing internal system details
    Given a locale handler with locale "en"
    And a response "The data is stored on our internal server db-prod-01.company.com in the customer_data database."
    And the LLM returns success=False with reasoning="Contains internal server names and database information" and cleaned_answer="The data is securely stored in our internal systems."
    When the sensitive info guard is executed
    Then the guard should reject the response
    And the reasoning should be "Contains internal server names and database information"
    And a cleaned answer "The data is securely stored in our internal systems." should be provided