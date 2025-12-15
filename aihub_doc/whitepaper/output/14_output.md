# Kapitel 14: Business-Prozessautomatisierung

Die vorangegangenen Kapitel haben dargelegt, wie KI-Agenten Wissen abrufen, verstehen und im Kontext interagieren. Doch
der wahre wirtschaftliche Hebel der digitalen Transformation liegt nicht im Chatten, sondern im Handeln. Unternehmen
bestehen aus Prozessen: Rechnungsfreigaben, Kunden-Onboarding, Beschwerdemanagement oder komplexe Antragsprüfungen in
der öffentlichen Verwaltung. Solange KI nur als passiver Auskunftsgeber fungiert, bleibt sie ein Assistenzsystem. Zur
treibenden Kraft wird sie erst, wenn sie aktive Verantwortung in End-to-End-Prozessen übernimmt.

Dieses Kapitel erläutert die Prozess-Engine des Swiss AI Hub. Es beschreibt, wie die Plattform eine Brücke schlägt
zwischen statischen Workflows, autonomen Agenten und der menschlichen Belegschaft. Ziel ist die Schaffung robuster
Geschäftsanwendungen, die Medienbrüche eliminieren, die Durchlaufzeiten drastisch verkürzen und dabei jederzeit
transparent und kontrollierbar bleiben.

## Auf einen Blick

- **Handlungsorientierte KI:** Transformation von passiven Chatbots zu aktiven Prozess-Akteuren, die Aufgaben in
  Drittsystemen autonom erledigen.
- **Zero-Config API-Generierung:** Automatische Erstellung von typensicheren REST-Endpunkten für jeden Prozess und
  Agenten, ohne manuellen Entwicklungsaufwand.
- **Hybride Intelligenz:** Nahtlose Eskalation von KI an Menschen («Human-in-the-Loop») und zurück, inklusive
  automatischer Wissensrückführung aus Experten-Chats.
- **Langlebige Persistenz:** Technische Unterstützung für Prozesse, die Tage oder Wochen andauern, ohne Ressourcen zu
  blockieren («State Management»).
- **Bidirektionale Integration:** Flexible Anbindung von Fachsystemen (ERP, CRM, eGovernment) sowohl durch aktive
  Agenten-Aufrufe als auch durch externe Trigger.

## Ganzheitliche Prozess-Orchestrierung und Dynamische Endpunkte

### Geschäftlicher Nutzen

Traditionelle Automatisierungslösungen (RPA) sind oft starr und scheitern an unstrukturiertern Daten oder Variabilität
im Prozess. Die Entwicklung massgeschneiderter Schnittstellen (APIs) für jeden neuen KI-Prozess ist zudem zeitaufwändig
und teuer. Unternehmen benötigen eine Agilität, bei der ein neuer Geschäftsprozess – etwa eine automatisierte
Posteingangsverarbeitung – sofort technisch verfügbar und integrierbar ist, ohne dass IT-Teams wochenlang neue
API-Gateways konfigurieren müssen. Dies reduziert die «Time-to-Market» für neue Automatisierungslösungen signifikant.

### Konzeptioneller Ansatz

Der Swiss AI Hub erweitert das Konzept des einzelnen Agenten um die übergeordnete Entität des **Prozesses**. Ein Prozess
ist ein langlebiger, zustandsbehafteter Ablauf, der mehrere Akteure koordiniert. Er fungiert als Dirigent, der Aufgaben
an spezialisierte «Worker»-Agenten delegiert. Ein zentrales Konzept ist hierbei die **Dienstentdeckung (Service
Discovery)**: Die Plattform erkennt automatisch, welche Fähigkeiten und Prozesse verfügbar sind, und stellt diese der
Aussenwelt dynamisch zur Verfügung. Dies eliminiert den manuellen Konfigurationsaufwand für Schnittstellen.

### Technische Umsetzung im Swiss AI Hub

Die Plattform realisiert dies durch intelligente Discovery-Dienste, die den NATS-Message-Bus kontinuierlich scannen:

- **Dynamische Endpunkt-Generierung:** Sobald ein neuer `Agenten-Bauplan` oder Prozess deployed wird, generieren der
  `AgentEndpointsDiscoveryService` und der `ProcessEndpointsDiscoveryService` automatisch entsprechende REST-Endpunkte.
  Ein Prozess ist sofort unter Pfaden wie `/api/v1/processes/{process_class}/{process_id}/{route}` erreichbar.
- **Typensicherheit durch Jambo:** Der integrierte «Jambo SchemaConverter» wandelt die Ereignisschemata der Prozesse zur
  Laufzeit in Pydantic-Modelle um. Dies garantiert, dass externe API-Aufrufe validiert werden, bevor sie die
  Geschäftslogik erreichen, und erzeugt automatisch eine aktuelle OpenAPI-Dokumentation (Swagger UI).
- **Fortsetzungspunkte:** Prozesse unterstützen sogenannte «Walkthrough IDs». Diese erlauben es externen Anwendungen
  (z.B. einem Web-Formular), einen laufenden Prozess an einem spezifischen Punkt wieder aufzunehmen, was für mehrstufige
  Genehmigungsworkflows essenziell ist.

## Hybride Entscheidungsarchitektur und Eskalation

### Geschäftlicher Nutzen

Ein vollständig autonomes System ist in regulierten Umfeldern oft weder rechtlich zulässig noch wünschenswert. Kritische
Entscheidungen – etwa im Kreditwesen oder bei behördlichen Verfügungen – erfordern menschliches Urteilsvermögen oder die
strikte Einhaltung deterministischer Regelwerke. Das Risiko von KI-Halluzinationen muss in Geschäftsprozessen eliminiert
werden. Unternehmen benötigen daher eine hybride Architektur, die KI für Vorarbeit und Analyse nutzt, die
Letztentscheidung aber bei Unsicherheiten nahtlos an Fachexperten übergibt, ohne dass der Prozesskontext verloren geht.

### Konzeptioneller Ansatz

Die Plattform setzt auf das **Delegationsmuster** (Delegation Pattern) und **Human-in-the-Loop**. Ein primärer
Orchestrator steuert den Ablauf. Stösst er auf Unsicherheiten, nutzt er das Prinzip des **«Expert Asking Agent»**: Die
KI versucht nicht zu raten, sondern triggert einen Eskalationspfad, der einen menschlichen Experten konsultiert. Die
Antwort des Experten löst nicht nur das aktuelle Problem, sondern wird als neues Wissen persistiert, sodass die KI beim
nächsten Mal autonom agieren kann.

### Technische Umsetzung im Swiss AI Hub

Dieses Muster wird technisch durch spezialisierte Ereignisse und Integrationskomponenten realisiert:

- **Agent-in-the-Loop:** Die Klasse `AgentInTheLoop` ermöglicht es einem Orchestrator, Sub-Agenten («Worker»)
  aufzurufen. Über Parameter wie `share_thread_id=True` teilen sich diese Agenten das Konversationsgedächtnis, sodass
  der Kontext erhalten bleibt, während `share_run_id=False` eine saubere technische Trennung der Ausführungen
  gewährleistet.
- **Human-in-the-Loop:** Ereignisse wie `HumanInTheLoop.request` unterbrechen den technischen Workflow und erzeugen eine
  persistente Aufgabe. Der Prozess verharrt in einem Wartezustand, bis ein `HumanInTheLoop.response`-Ereignis eintrifft.
- **Slack/Teams-Integration:** Im Szenario «Experte befragt Agenten» postet der Agent eine Frage in einen definierten
  Kanal (z.B. via Microsoft Teams). Antwortet der Experte im Thread, wird diese Antwort validiert, in die
  **Wissensdatenbank** zurückgespeichert (Learning Loop) und der Prozess automatisch fortgesetzt.

## Systemintegration und Integrationsmuster

### Geschäftlicher Nutzen

Ein Prozess, der keine Daten aus Fachsystemen lesen oder schreiben kann, bleibt isoliert. Der ROI von KI-Automatisierung
entsteht primär durch die Integration in die bestehende IT-Landschaft – sei es das Verbuchen im SAP, das Aktualisieren
eines Status im CRM oder das Ablegen eines Dokuments im eGovernment-Dossier (z.B. CMI Axioma oder Gever). Die
Herausforderung liegt darin, unterschiedliche Integrationsrichtungen (Push/Pull) und Latenzanforderungen
(Echtzeit/Batch) mit einer einheitlichen Plattform abzudecken, ohne für jedes System Punkt-zu-Punkt-Verbindungen bauen
zu müssen.

### Konzeptioneller Ansatz

Der Swiss AI Hub verfolgt eine umfassende Integrationsstrategie, die vier spezifische Muster unterstützt, um sowohl
Echtzeit-Interaktionen als auch Massendatenverarbeitung abzudecken. Die Plattform fungiert dabei als Drehscheibe, die
sowohl aktiv agieren (Outbound) als auch passiv gesteuert werden kann (Inbound).

### Technische Umsetzung im Swiss AI Hub

Die Plattform unterstützt technisch vier definierte Integrationsmuster:

1. **Direkte Agenten-API-Aufrufe (Outbound/Echtzeit):** Innerhalb eines `Agenten-Bauplans` nutzen Agenten
   Standard-Python-Bibliotheken (`httpx`, `aiohttp`), um externe REST-, SOAP- oder GraphQL-Schnittstellen synchron
   aufzurufen. Dies ist ideal für einfache Operationen wie «Kundenstatus abfragen».
2. **Plattform-API-Integration (Inbound/Echtzeit):** Externe Systeme nutzen die *Agent Interaction REST API*, um
   KI-Prozesse zu triggern. Der Traefik Reverse Proxy sichert diese Endpunkte via OAuth 2.0 oder API-Keys ab. Ein
   typischer Fall ist ein Webhook aus einem Formularserver, der eine KI-Prüfung startet.
3. **Daten-Pipelines (Inbound/Batch):** Für die Synchronisation grosser Datenmengen (z.B. nächtlicher Import von
   SharePoint-Dokumenten) nutzt die Plattform **Dagster**. Diese Pipelines extrahieren, transformieren und laden Daten
   in die **Vektordatenbank** (Milvus), damit RAG-Prozesse stets auf aktuellen **Unternehmensdaten** operieren.
4. **Model Context Protocol (MCP):** Für Entwickler-Workflows stellt die Plattform einen MCP-Server bereit. Dies erlaubt
   es IDEs und KI-Coding-Assistenten (wie Cursor oder Claude Code), den Systemzustand abzufragen und die API-Struktur
   dynamisch zu explorieren.

## Langläufer-Prozesse und State Management

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
- **Observation:** Über integrierte Monitoring-Tools können Administratoren den Status langlaufender Prozesse einsehen.
  Sie erkennen sofort, an welchem Schritt ein Prozess wartet (z.B. «Blocked by User») und können bei Bedarf eingreifen.

## Zusammenfassung

Mit der Business-Prozessautomatisierung transformiert der Swiss AI Hub KI von einem Werkzeug zur Texterstellung in eine
Engine zur Wertschöpfung. Durch die enge Verzahnung von deterministischen Workflows, dynamischer API-Generierung und
flexiblen Integrationsmustern entstehen robuste Anwendungen, die echte Arbeit erledigen – sicher, nachvollziehbar und
tief integriert in die Schweizer Unternehmenslandschaft.
