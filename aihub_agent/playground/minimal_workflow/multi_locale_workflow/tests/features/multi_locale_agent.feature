Feature: Multi Locale Agent
  test for MultiLocaleAgent

  Scenario: Test Multi Locale Agent
    Given a MultiLocaleAgent runner

    When a StartEvent is sent with locale "en"

    Then a StartEvent is present with locale "en"
    And a StopEvent is present