Feature: Multi Locale Agent
  test for MultiLocaleAgent

  Scenario: Test en
    Given a MultiLocaleAgent runner with locale_path "myagent.myscope.test"
    When a StartEvent is sent with locale "en"
    Then an event is present with payload "This is an english scope test"
    And a StopEvent is present

  Scenario: Test de
    Given a MultiLocaleAgent runner with locale_path "myagent.myscope.test"
    When a StartEvent is sent with locale "de"
    Then an event is present with payload "Das ist ein deutscher Scope test"
    And a StopEvent is present