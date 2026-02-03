# Plattform-Überblick – Die Swiss AI-Hub-Lösung

Der Swiss AI Hub definiert sich grundlegend anders als herkömmliche Angebote am Markt. Er ist weder ein reines
Software-Framework, das jahrelange interne Entwicklungsarbeit erfordert, noch ein externer SaaS-Dienst, der die
Datenhoheit untergräbt. Vielmehr handelt es sich um eine vollständige Enterprise-KI-Infrastruktur, die als
schlüsselfertiges Produkt konzipiert ist. Unternehmen erhalten ein System, das sie selbst besitzen, kontrollieren und
innerhalb von 30 Minuten in der eigenen Umgebung in Betrieb nehmen können. Dieser Ansatz schliesst die Lücke zwischen
schnellen Prototypen und einem skalierbaren, sicheren Produktionsbetrieb, indem er die komplexen Infrastrukturfragen
bereits im Kern löst.

## Auf einen Blick

- **Infrastruktur als Produkt:** Eine «Batteries-Included»-Plattform, die alle notwendigen Komponenten wie LLM-Gateway,
  Datenbanken und Monitoring vorkonfiguriert mitbringt.
- **Skalierbares Stufenmodell:** Ein strukturierter Pfad ermöglicht den organischen Übergang von sicherem KI-Zugang über
  kontextbezogenes Wissen (RAG) bis zur Prozessautomatisierung.
- **Plattform-SDK-Synergie:** Die strikte Trennung erlaubt es Entwicklern, sich auf die Geschäftslogik zu konzentrieren,
  während die Plattform Sicherheit und Betrieb übernimmt.
- **Lösung des «Day 2»-Problems:** Kritische Betriebsaufgaben wie Kostenkontrolle, PII-Anonymisierung und Audit-Trails
  sind bereits im Standard implementiert.
- **Strategische Unabhängigkeit:** Dank Apache 2.0 Lizenz und modell-agnostischer Architektur wird ein Vendor-Lock-in
  effektiv ausgeschlossen.

## Enterprise-Infrastruktur «Out-of-the-Box»

### Geschäftlicher Nutzen

Für Unternehmen stellt die Zusammenstellung eines KI-Stacks oft eine unüberwindbare Einstiegshürde dar. Die Evaluierung
und Integration von Vektordatenbanken, API-Gateways und Monitoring-Tools bindet IT-Ressourcen über Monate. Der Swiss AI
Hub eliminiert diese «Integrationssteuer». Da die Plattform alle notwendigen Komponenten für den Betrieb bereits
integriert hat, reduziert sich die Zeit bis zur Produktivsetzung drastisch. Dies ermöglicht es Organisationen, sich
sofort auf wertschöpfende Use Cases zu konzentrieren, anstatt Infrastruktur-Puzzles zu lösen. Zudem entfallen versteckte
Kosten und Lizenzgebühren für separate Drittanbieter-Komponenten.

### Konzeptioneller Ansatz

Das Prinzip lautet «Infrastructure as Product». Die Plattform wird nicht als loser Baukasten geliefert, sondern als
harmonisiertes Gesamtsystem, das wie ein «KI-Betriebssystem» fungiert. Es trennt strikt zwischen der stabilen
Plattform-Ebene und der flexiblen Anwendungs-Ebene (SDK). Während das SDK Entwicklern erlaubt, massgeschneiderte
Agenten-Baupläne zu entwerfen, übernimmt die Plattform automatisch die Schwerarbeit: Authentifizierung, Datenpersistenz,
Skalierung und Sicherheit. Ein Agent erbt seine Fähigkeiten zur Zugriffskontrolle und Überwachung automatisch durch den
Betrieb auf dem Hub.

### Technische Umsetzung im Swiss AI Hub

Technisch manifestiert sich dieser Ansatz in einer containerisierten Architektur, die via Docker Compose oder Kubernetes
orchestriert wird. Der Stack integriert Best-in-Class Komponenten: Das LLM-Gateway (LiteLLM) abstrahiert Modell-Provider
und verwaltet Failover-Logik. Als Vektordatenbank dient Milvus, während SeaweedFS den S3-kompatiblen Objektspeicher
bereitstellt. Die Sicherheit wird durch Presidio zur PII-Erkennung und eine OAuth2-Anbindung an bestehende
Identitätsanbieter (z.B. Azure AD) gewährleistet. Für die Observability sammelt OpenTelemetry Metriken, die in Phoenix
visualisiert werden.

## Ein Stufenmodell für skalierbare KI-Adoption

### Geschäftlicher Nutzen

Die Einführung von KI scheitert oft an einem «Alles-oder-Nichts»-Ansatz. Organisationen versuchen, komplexe Systeme zu
bauen, bevor die Grundlagen etabliert sind. Der Swiss AI Hub begegnet diesem Risiko mit einem integrierten
Reifegradmodell. Dies erlaubt es Unternehmen, mit geringem Risiko zu starten und die Komplexität schrittweise zu
steigern. Mitarbeiter bauen Vertrauen in die Technologie auf, während die Organisation sukzessive Kompetenzen
entwickelt. Investitionen wachsen linear mit dem geschäftlichen Mehrwert, nicht exponentiell mit der technischen
Komplexität.

### Konzeptioneller Ansatz

Die Plattform unterstützt vier logische Evolutionsstufen, die den organisatorischen Reifeprozess begleiten:

1. **Stufe 1 (Sicherer Zugang):** Zentraler, protokollierter Zugang zu LLMs via Web-Interface.
2. **Stufe 1+ (Integration):** KI-Funktionen in gewohnten Umgebungen wie MS Teams oder Slack.
3. **Stufe 2 (Kontext):** Einführung von Wissensdatenbanken (RAG), damit Agenten-Profile auf Unternehmensdaten zugreifen
   können.
4. **Stufe 3 (Prozesse):** Orchestrierung komplexer Abläufe, in denen KI-Agenten und Menschen zusammenarbeiten.

### Technische Umsetzung im Swiss AI Hub

Für **Stufe 1** bietet der Hub die Open-WebUI mit Streaming-Support. **Stufe 1+** nutzt das Azure Bot Framework, um
Kanäle wie Teams oder Outlook anzubinden. In **Stufe 2** kommen automatisierte Daten-zu-Wissen-Pipelines zum Einsatz:
Dokumente werden mit Docling geparst und als Vektoren in Milvus abgelegt. **Stufe 3** aktiviert die
Prozess-Orchestrierungs-Engine, die Zustände in MongoDB verwaltet und Aufgaben zwischen KI-Agenten und menschlichen
Benutzern über eine dedizierte Prozess-UI koordiniert. Integrationen zu Power Automate oder n8n ermöglichen hierbei die
Anbindung an Legacy-Systeme.

## Strategische Unabhängigkeit und der «Day 2»-Vorteil

### Geschäftlicher Nutzen

Ein zentrales Versprechen des Swiss AI Hub ist der Investitionsschutz durch Vermeidung von Vendor-Lock-in. Proprietäre
Plattformen binden Kunden oft durch geschlossene Ökosysteme und unvorhersehbare «Per-User»-Gebühren. Da der Swiss AI Hub
unter der Apache 2.0 Lizenz bereitgestellt wird, gehört der Code dem Kunden. Es fallen keine Software-Lizenzgebühren an.
Zudem adressiert die Plattform proaktiv die Probleme des «Day 2»: Kostenexplosionen werden durch zentrale Budgets
verhindert, Compliance-Risiken durch Audit-Trails minimiert und die Wartbarkeit durch standardisierte Tracing-Tools
gesichert.

### Konzeptioneller Ansatz

Die Architektur ist radikal «modell-agnostisch» und «provider-unabhängig». Sie abstrahiert die Intelligenz (das LLM) von
der Anwendung. Dies ermöglicht es, flexibel zwischen Anbietern wie OpenAI, Google oder lokal gehosteten Modellen (wie
Mistral via vLLM) zu wechseln. Das System ist durch offene Protokolle anschlussfähig, etwa durch das Model Context
Protocol (MCP), welches externen Entwicklungstools sicheren Zugriff auf Plattform-Ressourcen gewährt. So bleibt die
Organisation technologisch agil und behält die volle Kostenkontrolle.

### Technische Umsetzung im Swiss AI Hub

Diese Freiheit wird durch die konsequente Nutzung offener Standards realisiert. Das LLM-Gateway bietet eine
vereinheitlichte Schnittstelle und trackt die Token-Nutzung für eine präzise Kostenzuordnung pro Team. PII-Daten werden
durch Presidio anonymisiert, bevor sie externe Netze erreichen. Dank des SDKs können Agenten-Baupläne deterministisch
mit dem `AgentTestRunner` geprüft werden, was die Qualitätssicherung professionalisiert. Da der gesamte Stack auf
bewährten Open-Source-Technologien basiert, bleibt das System vollständig auditierbar und kann bei Bedarf ohne
Internetverbindung (Air-Gapped) betrieben werden.
