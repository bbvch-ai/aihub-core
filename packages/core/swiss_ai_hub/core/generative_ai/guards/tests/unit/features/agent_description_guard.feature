Feature: Agent Description Guard

  Scenario: Validate agent description guard with valid inputs
    Given a locale handler with locale "de"
    And an agent description "Test agent description"
    And a user query "Test user query"
    And the following messages:
      | role      | content         |
      | USER      | User message 1  |
      | ASSISTANT | Agent message 1 |
    When the agent description guard is executed
    Then structured_predict should be called
    And structured_predict should be called with prompt:
      """
      Die Beschreibung eines Agenten lautet wiefolgt:
      <Agentenbeschreibung>
      Test agent description
      </Agentenbeschreibung>
      Der Agent hat eventuell Zugriff auf weitere Informationsquellen, die ihm bei der Beantwortung der Frage helfen könnten.
      Entscheide, ob die vom Benutzer gestellte Frage im Kontext des Gespräches diesem Agenten gestellt werden soll. Lasse alle Fragen zu, die
      möglicherweise in den Themenbereich des Agenten fallen. Blockiere alle Fragen, die ganz offensichtlich
      überhaupt nichts mit dem Agenten zu tun haben. Im zweifelsfall entscheide dich für das Zulassen der Frage.
      <Benutzer Anfrage>
      Test user query
      </Benutzer Anfrage>
      <vergangener Gesprächsverlauf>
      <Benutzer>
      User message 1
      </Benutzer>
      <Agent>
      Agent message 1
      </Agent>

      </vergangener Gesprächsverlauf>
      Ihre finale Ausgabe muss ausschliesslich ein JSON-Objekt mit genau den beiden Schlüsseln "success" und "reasoning" sein. Wiederholen Sie nicht das gesamte JSON-Schema oder fügen zusätzliche Meta-Informationen hinzu.
      """
