# Kapitel 14: Business-Prozessautomatisierung

Die vorangegangenen Kapitel haben dargelegt, wie KI-Agenten Wissen abrufen, verstehen und im Kontext interagieren. Doch
der wahre wirtschaftliche Hebel der digitalen Transformation liegt nicht im Chatten, sondern im Handeln. Unternehmen
bestehen aus Prozessen: Rechnungsfreigaben, Kunden-Onboarding, Beschwerdemanagement oder komplexe Antragsprüfungen in
der öffentlichen Verwaltung. Solange KI nur als passiver Auskunftsgeber fungiert, bleibt sie ein Assistenzsystem. Zur
treibenden Kraft wird sie erst, wenn sie aktive Verantwortung in End-to-End-Prozessen übernimmt.

Dieses Kapitel erläutert die Prozess-Engine des Swiss AI Hub, welche die höchste Stufe des technologischen
Reifegradmodells (Stufe 3) darstellt. Es beschreibt, wie die Plattform eine Brücke schlägt zwischen statischen
Workflows, autonomen Agenten und der menschlichen Belegschaft. Ziel ist die Schaffung robuster Geschäftsanwendungen, die
Medienbrüche eliminieren, die Durchlaufzeiten drastisch verkürzen und dabei jederzeit transparent und kontrollierbar
bleiben.

## Auf einen Blick

- **Ganzheitliche Orchestrierung:** Transformation von passiven Chatbots zu aktiven Prozess-Akteuren, die Aufgaben
  zwischen KI, Menschen und Programmen koordinieren.
- **Zero-Config API-Generierung:** Automatische Erstellung von typensicheren REST-Endpunkten für jeden Prozess und
  Agenten, was die Integrationszeit massiv verkürzt.
- **Hybride Intelligenz:** Nahtlose Eskalation von KI an Menschen via «Human-in-the-Loop» oder «Bot-in-the-Loop»
  (Teams/Slack), inklusive automatischer Wissensrückführung.
- **Langlebige Persistenz:** Technische Unterstützung für Prozesse, die Tage oder Wochen andauern, durch persistentes
  State-Management auf Basis von NATS JetStream.
- **Vier Integrationsmuster:** Flexible Anbindung von Fachsystemen (ERP, CRM, eGovernment) sowohl durch aktive
  Agenten-Aufrufe als auch durch automatisierte Daten-Pipelines.

## Ganzheitliche Orchestrierung und agentische Prozesse

### Geschäftlicher Nutzen

Traditionelle Automatisierungslösungen (RPA) sind oft starr und scheitern an unstrukturierten Daten oder Variabilität im
Prozess. Die Entwicklung massgeschneiderter Schnittstellen (APIs) für jeden neuen KI-Prozess ist zudem zeitaufwändig und
teuer. Unternehmen benötigen eine Agilität, bei der ein neuer Geschäftsprozess – etwa eine automatisierte
Posteingangsverarbeitung – sofort technisch verfügbar und integrierbar ist, ohne dass IT-Teams wochenlang neue
API-Gateways konfigurieren müssen. Dies reduziert die «Time-to-Market» für neue Automatisierungslösungen signifikant und
ermöglicht es, komplexe Abläufe als dynamische Kollaborationen zu gestalten.

### Konzeptioneller Ansatz

Der Swiss AI Hub erweitert das Konzept des einzelnen Agenten um die übergeordnete Entität des «agentischen Prozesses».
Ein Prozess ist ein langlebiger, zustandsbehafteter Ablauf, der die Zusammenarbeit zwischen vier Entitätstypen
koordiniert: Agenten (KI-Logik), Menschen (Entscheidungsträger), Programme (externe APIs) und andere Prozesse. Ein
Prozess fungiert dabei als Dirigent, der Aufgaben an spezialisierte «Worker» delegiert, anstatt die Logik selbst
auszuführen. Ein zentrales Konzept ist hierbei die Dienstentdeckung (Service Discovery): Die Plattform erkennt
automatisch, welche Fähigkeiten verfügbar sind, und stellt diese der Aussenwelt dynamisch zur Verfügung.

### Technische Umsetzung im Swiss AI Hub

Die Plattform realisiert dies durch die Basisklasse `AgenticProcess` und intelligente Discovery-Dienste, die den
NATS-Message-Bus kontinuierlich scannen. Entwickler definieren Prozessschritte mittels des `@process_step()`-Decorators,
welcher als Delegationspunkt fungiert.

Sobald ein neuer `Agenten-Bauplan` oder Prozess bereitgestellt wird, generiert der `ProcessEndpointsDiscoveryService`
automatisch entsprechende REST-Endpunkte unter Pfaden wie `/api/v1/processes/{process_class}/{process_id}/{route}`. Der
integrierte «Jambo SchemaConverter» wandelt die Ereignisschemata der Prozesse zur Laufzeit in Pydantic-Modelle um. Dies
garantiert, dass externe API-Aufrufe validiert werden, bevor sie die Geschäftslogik erreichen, und erzeugt automatisch
eine aktuelle OpenAPI-Dokumentation (Swagger UI).

## Hybride Entscheidungsarchitektur und Kollaborationsmuster

### Geschäftlicher Nutzen

Ein vollständig autonomes System ist in regulierten Umfeldern oft weder rechtlich zulässig noch wünschenswert. Kritische
Entscheidungen – etwa im Kreditwesen oder bei behördlichen Verfügungen – erfordern menschliches Urteilsvermögen oder die
strikte Einhaltung deterministischer Regelwerke. Das Risiko von KI-Halluzinationen muss eliminiert werden. Unternehmen
benötigen daher eine hybride Architektur, die KI für Vorarbeit und Analyse nutzt, die Letztentscheidung aber bei
Unsicherheiten nahtlos an Fachexperten übergibt, ohne dass der Prozesskontext verloren geht.

### Konzeptioneller Ansatz

Die Plattform setzt auf das Delegationsmuster (Delegation Pattern) und zwei Formen der menschlichen Integration. Beim
«Human-in-the-Loop» (HITL) fordert der Agent über die Plattform-Oberfläche eine Eingabe an. Beim «Bot-in-the-Loop»
(BITL) erfolgt die Eskalation über Kollaborations-Tools wie Microsoft Teams oder Slack. Stösst der Orchestrator auf
Unsicherheiten, nutzt er das Prinzip des «Expert Asking Agent»: Die KI versucht nicht zu raten, sondern triggert einen
Eskalationspfad. Die Antwort des Experten löst nicht nur das aktuelle Problem, sondern wird als neues Wissen in der
Wissensdatenbank persistiert (Learning Loop), sodass die KI beim nächsten Mal autonom agieren kann.

### Technische Umsetzung im Swiss AI Hub

Dieses Muster wird technisch durch spezialisierte Ereignisse realisiert:

- **Agent-in-the-Loop (AITL):** Die Klasse `AgentInTheLoop` ermöglicht es einem Orchestrator, Sub-Agenten aufzurufen.
  Über Parameter wie `share_thread_id=True` teilen sich diese Agenten das Konversationsgedächtnis, während
  `share_run_id=False` eine saubere technische Trennung gewährleistet.
- **Human-in-the-Loop:** Ereignisse wie `HumanInTheLoop.request` unterbrechen den technischen Workflow und erzeugen eine
  Aufgabe. Der Prozess verharrt in einem Wartezustand, bis ein `HumanInTheLoop.response`-Ereignis eintrifft.
- **Bot-in-the-Loop:** Via `BotInTheLoop.invoke()` postet der Agent eine Frage in einen Slack- oder Teams-Kanal. Die
  Antwort des Experten im Thread wird vom System erfasst, validiert und der Prozess automatisch fortgesetzt.

## Systemintegration und Integrationsmuster

### Geschäftlicher Nutzen

Ein Prozess, der keine Daten aus Fachsystemen lesen oder schreiben kann, bleibt isoliert. Der ROI von KI-Automatisierung
entsteht primär durch die Integration in die bestehende IT-Landschaft – sei es das Verbuchen im SAP, das Aktualisieren
eines Status im CRM oder das Ablegen eines Dokuments im eGovernment-Dossier (z. B. CMI Axioma oder Gever). Die
Herausforderung liegt darin, unterschiedliche Integrationsrichtungen (Push/Pull) und Latenzanforderungen
(Echtzeit/Batch) mit einer einheitlichen Plattform abzudecken, ohne für jedes System Punkt-zu-Punkt-Verbindungen bauen
zu müssen.

### Konzeptioneller Ansatz

Der Swiss AI Hub verfolgt eine umfassende Integrationsstrategie, die vier spezifische Muster unterstützt, um sowohl
Echtzeit-Interaktionen als auch Massendatenverarbeitung abzudecken. Die Plattform fungiert dabei als Drehscheibe, die
sowohl aktiv agieren (Outbound) als auch passiv gesteuert werden kann (Inbound).

### Technische Umsetzung im Swiss AI Hub

Die Plattform unterstützt technisch vier definierte Integrationsmuster:

1. **Direkte Agenten-API-Aufrufe (Outbound):** Innerhalb eines `Agenten-Bauplans` nutzen Agenten Bibliotheken wie
   `httpx`, um externe REST-, SOAP- oder GraphQL-Schnittstellen synchron aufzurufen (z. B. «Kundenstatus abfragen»).
2. **Plattform-API-Integration (Inbound):** Externe Systeme nutzen die Agent Interaction REST API, um Prozesse zu
   triggern. Der Traefik Reverse Proxy sichert diese Endpunkte via OAuth 2.0 oder API-Keys ab.
3. **Daten-Pipelines (Batch):** Für die Synchronisation grosser Datenmengen (z. B. aus SharePoint) nutzt die Plattform
   Dagster. Diese Pipelines laden Daten in die Wissensdatenbank, damit RAG-Prozesse stets auf aktuellen
   Unternehmensdaten operieren.
4. **Model Context Protocol (MCP):** Für Entwickler-Workflows stellt die Plattform einen MCP-Server bereit. Dies erlaubt
   es KI-Assistenten, den Systemzustand abzufragen und die API-Struktur dynamisch zu explorieren.

## Langläufer-Prozesse und persistente Zustandsverwaltung

### Geschäftlicher Nutzen

Reale Geschäftsprozesse sind selten in Millisekunden abgeschlossen. Eine Vertragsprüfung kann Tage dauern, weil auf die
Unterschrift eines Vorgesetzten gewartet werden muss. Technische Systeme dürfen während solcher Wartezeiten keine
Ressourcen blockieren oder in Timeouts laufen. Die Zuverlässigkeit eines Automatisierungssystems misst sich daran, ob es
Prozesse über Tage oder Wochen stabil halten kann, ohne den Kontext zu verlieren, selbst wenn Server neu gestartet oder
aktualisiert werden.

### Konzeptioneller Ansatz

Der Swiss AI Hub behandelt Zeit als fundamentalen Faktor. Die Architektur ist auf Asynchronität und Persistenz
ausgelegt. Ein Prozess, der auf ein externes Ereignis wartet, verbraucht keine Rechenleistung («Sleep Mode»). Sein
gesamter Zustand – Variablen, bisherige Schritte, Dokumente – wird serialisiert und sicher in der Datenbank abgelegt.
Sobald das erwartete Ereignis eintritt, wird der Prozess «rehydriert» und setzt die Arbeit exakt an der Stelle fort, an
der er pausiert hat.

### Technische Umsetzung im Swiss AI Hub

Die technische Basis bildet eine Kombination aus NATS JetStream und robusten Persistenz-Schichten:

- **Event-Sourcing:** Jeder Schritt im Prozess erzeugt ein Ereignis. Der Zustand des Prozesses ist die Summe dieser
  Ereignisse. Dies ermöglicht nicht nur das Pausieren, sondern auch eine lückenlose Auditierung («Wer hat wann was
  genehmigt?»).
- **Wiederherstellung:** Da der Zustand persistent ist, überleben Prozesse auch Neustarts der Container-Infrastruktur
  oder Updates der Plattform.
- **Observation:** Über integrierte Monitoring-Tools (Phoenix/SigNoz) können Administratoren den Status langlaufender
  Prozesse einsehen. Sie erkennen sofort, an welchem Schritt ein Prozess wartet (z. B. «Blocked by User») und können bei
  Bedarf manuell eingreifen.
