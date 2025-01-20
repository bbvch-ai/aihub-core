Feature: Multi Locale Agent
  test for MultiLocaleAgent

  Scenario: Test en
    Given a MultiLocaleAgent runner

    When a StartEvent is sent with locale "en"

    Then a StartEvent is present with locale "en"
    And a EventA is present with payload "This is an english test"
    And a StopEvent is present

  Scenario: Test de
    Given a MultiLocaleAgent runner

    When a StartEvent is sent with locale "de"

    Then a StartEvent is present with locale "de"
    And a EventA is present with payload "Das ist ein deutscher Test"
    And a StopEvent is present