Feature: Multi Locale Agent
  test for MultiLocaleAgent

  Scenario: Test en
    Given a MultiLocaleAgent runner

    When a StartEvent is sent with locale "en"

    Then a StartEvent is present with locale "en"
    And an event is present with payload "This is a prompt in english"
    And a StopEvent is present

  Scenario: Test de
    Given a MultiLocaleAgent runner

    When a StartEvent is sent with locale "de"

    Then a StartEvent is present with locale "de"
    And an event is present with payload "Das ist ein test prompt auf deutsch"
    And a StopEvent is present