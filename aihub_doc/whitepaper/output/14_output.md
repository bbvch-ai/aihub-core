# Kapitel 14: Business-Prozessautomatisierung

## Von der Interaktion zur Orchestrierung

Während sich die vorangegangenen Kapitel primär auf die Fähigkeiten einzelner KI-Agenten und deren Interaktion mit
Nutzern konzentrierten, erfordert die Realität komplexer Organisationen weit mehr als nur intelligente Dialogsysteme.
Ein realer Geschäftsfall – sei es die Prüfung eines Baugesuchs, die Bearbeitung eines Schadensfalls bei einer
Versicherung oder das Onboarding eines neuen Mitarbeitenden – ist selten ein atomarer Schritt. Es handelt sich vielmehr
um langlaufende Vorgänge, die sich über Tage oder Wochen erstrecken, diverse IT-Systeme involvieren und zwingend
menschliche Kontrollpunkte benötigen.

Der Swiss AI Hub erweitert daher das Konzept des autonomen Agenten um die Ebene der **Prozess-Orchestrierung**. Hierbei
agiert die Plattform nicht nur als reaktiver Antwortgeber, sondern als aktive Workflow-Engine, die deterministische
Abläufe steuert. Diese Automatisierungsschicht verbindet die adaptive Intelligenz von Sprachmodellen mit der notwendigen
Verlässlichkeit starrer Geschäftsprozesse (Business Process Management) und ermöglicht so eine echte
End-to-End-Bearbeitung ohne Medienbrüche.

## Persistente Workflows und Status-Management

### Die Herausforderung langlaufender Transaktionen

In klassischen KI-Implementierungen ist der Kontext oft flüchtig: Wird das Browserfenster geschlossen oder startet ein
Server neu, ist der Zustand der Verarbeitung verloren. Für geschäftskritische Prozesse ist dies inakzeptabel. Wenn ein
Antrag auf eine behördliche Genehmigung wartet, darf der technische Prozess nicht abbrechen, nur weil die Wartezeit die
Timeouts einer Standard-HTTP-Verbindung überschreitet. Organisationen benötigen eine Architektur, die den Zustand eines
Vorgangs («State») über beliebige Zeiträume hinweg sicher speichert und verwaltet.

### Zustandsbehaftete Prozessarchitektur

Der Swiss AI Hub löst diese Anforderung durch eine strikte Trennung von **Prozessen** und **Agenten**. Während Agenten
oft reaktiv auf eine direkte Eingabe antworten, sind Prozesse als langlebige, zustandsbehaftete Entitäten konzipiert.
Die Plattform nutzt hierfür ein robustes State-Management, das jeden Fortschritt persistiert. Ein Prozess kann einen
Teilschritt erledigen – beispielsweise die Klassifizierung eines eingehenden Dokuments – und sich danach «schlafen
legen», während er auf ein externes Ereignis oder eine menschliche Freigabe wartet.

Technisch basiert dies auf einer ereignisgesteuerten Architektur via NATS JetStream. Der Zustand des Prozesses wird
nicht im Arbeitsspeicher gehalten, sondern als Sequenz von Ereignissen in der Datenbank abgebildet. Dies garantiert
Resilienz: Selbst wenn die physische Infrastruktur (Server, Container) während eines laufenden Vorgangs neu gestartet
wird, nimmt der Prozess seine Arbeit exakt an der Stelle wieder auf, an der er unterbrochen wurde. Externe Systeme
können über definierte Endpunkte (`/processes/{process_id}/`) jederzeit den aktuellen Status abfragen oder den Prozess
fortsetzen, ohne sich um die technische Verfügbarkeit der darunterliegenden Rechenknoten sorgen zu müssen.

## Nahtlose Integration via Dynamische Endpunkte

### Überwindung der Schnittstellen-Starre

Eine der grössten Hürden bei der Automatisierung ist die Anbindung an die bestehende Applikationslandschaft (ERP, CRM,
Fachverfahren). Traditionell erfordert jede neue Automatisierung die manuelle Entwicklung von API-Wrappern («Glue
Code»), damit ein externes System wie SAP oder CMI Axioma mit der KI-Lösung kommunizieren kann. Dies ist zeitaufwändig
und wartungsintensiv. IT-Abteilungen stehen oft vor dem Problem, dass die KI-Plattform zwar leistungsfähig ist, aber als
isolierter Silo neben den führenden Systemen existiert.

### Automatische Generierung der API-Schicht

Der Swiss AI Hub eliminiert diesen Integrationsaufwand durch das Konzept der **Dynamischen Endpunkte**. Die Plattform
setzt auf intelligente Discovery-Dienste (`AgentEndpointsDiscoveryService` und `ProcessEndpointsDiscoveryService`), die
kontinuierlich den internen Message Bus überwachen. Sobald ein neuer Prozess definiert oder ein neuer Agent deployt
wird, generiert das integrierte API-Gateway vollautomatisch die passenden REST-Schnittstellen.

Das System analysiert dabei die Ereignis-Schemata der Komponenten und übersetzt diese mittels des «Jambo
SchemaConverter» in validierte Pydantic-Modelle. Das Ergebnis sind typensichere, dokumentierte API-Endpunkte, die sofort
verfügbar sind. Ein Fachverfahren kann somit einen KI-Prozess direkt über einen Standard-POST-Request anstossen (z.B.
`/api/v1/processes/invoice_processor/start`), ohne dass ein Entwickler zuvor eine Schnittstelle programmieren musste.

Die Plattform unterstützt hierbei vier primäre Integrationsmuster für maximale Flexibilität:

1. **Direkte Agenten-Aufrufe (Outbound):** Agenten rufen aktiv externe REST/SOAP-Schnittstellen auf (z.B. via `httpx`),
   um Daten zu lesen oder Aktionen in Drittsystemen auszulösen.
2. **Plattform-API-Integration (Inbound):** Externe Systeme triggern Agenten oder Prozesse via REST, um KI-Aufgaben zu
   delegieren.
3. **Daten-Pipelines (Batch):** Kontinuierliche Synchronisation grosser Datenmengen via Dagster für leseintensive
   Szenarien.
4. **MCP-Integration:** Anbindung von Entwickler-Tools über das Model Context Protocol zur Systeminspektion.

## Hybride Intelligenz und Eskalationspfade

### Die Grenzen der Automatisierung erkennen

Vollautomatisierung ist nicht immer das Ziel. In vielen Szenarien ist die hybride Zusammenarbeit zwischen KI und Mensch
(«Human-in-the-Loop») regulatorisch vorgeschrieben oder qualitativ notwendig. Ein System, das bei Unsicherheiten
halluziniert oder stur falsche Entscheidungen trifft, gefährdet die Compliance. Die Business-Anforderung lautet daher:
Automatisierung der Routine, Eskalation der Ausnahme.

### Das Expert Asking Agent Muster

Der Swiss AI Hub implementiert diese Logik durch standardisierte Delegationsmuster. Ein besonders leistungsfähiges
Szenario ist die Zusammenarbeit eines «Expert Grounded Agent» mit einem «Expert Asking Agent».

Kann der Grounded Agent eine Benutzeranfrage basierend auf der Wissensdatenbank nicht zufriedenstellend beantworten,
initiiert er eine Eskalation. Anstatt zu halluzinieren, delegiert er die Aufgabe an den Expert Asking Agent. Dieser
formuliert die offene Frage und leitet sie über integrierte Kanäle (wie Slack oder MS Teams) an definierte menschliche
Experten weiter. Der Prozess wechselt in einen Wartezustand.

Sobald der Experte im Chat antwortet, geschieht zweierlei: Erstens wird die Antwort genutzt, um den aktuellen Fall
fortzusetzen. Zweitens speichert der Agent diese neue Information – nach einer optionalen Prüfung auf Vollständigkeit –
direkt in die Wissensdatenbank zurück. Damit lernt das System permanent dazu: Was heute eine Ausnahme war, die
menschliches Eingreifen erforderte, ist morgen Teil des automatisierten Standardwissens.

### Human-in-the-Loop Genehmigungen

Für formelle Freigaben nutzt die Plattform dedizierte `HumanInTheLoop`-Events. Ein Agent kann einen Workflow pausieren
und eine explizite Entscheidung anfordern («Soll die Zahlung ausgelöst werden?»). Erst wenn das entsprechende
`response`-Event durch einen autorisierten Nutzer eintrifft, setzt der Workflow fort. Dies ermöglicht auch mehrstufige
Genehmigungsketten, die komplexe Hierarchien abbilden.

## Orchestrierung komplexer Multi-Agenten-Systeme

### Zerlegung komplexer Probleme

Monolithische KI-Modelle neigen dazu, bei komplexen, mehrstufigen Aufgaben an Präzision zu verlieren. Ein effektiver
Business-Prozess erfordert oft unterschiedliche Kompetenzen: Ein Schritt benötigt mathematische Präzision, ein anderer
kreatives Schreiben, ein dritter strikte Regelbefolgung.

### Router und Worker Architektur

Die Plattform ermöglicht den Aufbau von **Multi-Agenten-Systemen**, die nach dem «Teile und Herrsche»-Prinzip arbeiten.
Ein zentraler **Orchestrator-Agent** analysiert die eingehende Anfrage und delegiert Teilaufgaben an spezialisierte
**Worker-Agenten**.

Technisch wird dies über das `AgentInTheLoop`-Muster realisiert, welches verschiedene Ausführungsstrategien erlaubt:

- **Sequenzielle Ketten:** Die Ausgabe von Agent A (z.B. Datenextraktion aus einer Rechnung) dient als Eingabe für Agent
  B (z.B. Prüfung auf Betrugsmuster).
- **Parallele Ausführung (Fan-Out):** Ein Orchestrator delegiert Teilaufgaben gleichzeitig an mehrere Agenten – etwa die
  Prüfung eines Vertrags durch einen juristischen Bot und einen finanziellen Bot parallel – und aggregiert die
  Ergebnisse («Fan-In») zu einer finalen Empfehlung.
- **Routing:** Ein spezialisierter Router entscheidet basierend auf dem Dokumententyp (z.B. «Finanzen» vs. «Recht»),
  welcher Spezialagent konsultiert wird.

Dabei lässt sich granular steuern, ob Kontexte geteilt werden. Mittels `share_thread_id=True` können Sub-Agenten auf die
bisherige Konversation zugreifen, während `share_run_id=False` eine saubere Trennung der Ausführungsstränge
gewährleistet.

## Transparenz und Prozess-Monitoring

### Überwachung jenseits von System-Logs

Für Prozessverantwortliche ist es entscheidend, nicht nur zu wissen, ob das System technisch läuft, sondern wo fachliche
Vorgänge stehen. Hängen Anträge in der Freigabe? Wie lange dauert die KI-Bearbeitung im Durchschnitt?

### Prozess-Observability

Da jeder Prozessschritt auf der Plattform diskrete Ereignisse emittiert, bietet der Swiss AI Hub eine granulare
Nachverfolgbarkeit. Über die automatisch generierten Prozess-Endpunkte lassen sich Statusinformationen in Echtzeit
abrufen. Dies ermöglicht den Aufbau von Dashboards, die Flaschenhälse in der Prozesskette visualisieren. Kombiniert mit
der Deep Observability (OpenTelemetry) können Administratoren bei Fehlern exakt nachvollziehen, bei welchem
Entscheidungsschritt oder externen API-Aufruf ein Prozess gescheitert ist, und ihn gegebenenfalls gezielt neu anstossen.

Zusammenfassend transformiert der Swiss AI Hub KI von einem reinen Dialogpartner zu einem verlässlichen Motor für die
Prozessautomatisierung. Durch die Verbindung von persistentem State-Management, dynamischer Integration und
intelligenten Eskalationsstrategien werden KI-Fähigkeiten tief und sicher in die Wertschöpfungskette des Unternehmens
eingebettet.
