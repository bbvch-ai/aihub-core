Feature: Multi Locale Agent
  test for MultiLocaleAgent

  Scenario: Test en
    Given a MultiLocaleAgent runner with locale_path "agent.thought.searching_knowledge"
    When a StartEvent is sent with locale "en"
    Then an event is present with payload "Searching for knowledge"
    And a StopEvent is present

  Scenario: Test de
    Given a MultiLocaleAgent runner with locale_path "agent.thought.searching_knowledge"
    When a StartEvent is sent with locale "de"
    Then an event is present with payload "Suche nach Wissen"
    And a StopEvent is present