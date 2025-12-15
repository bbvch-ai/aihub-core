# Kapitel 11: Integration und Interoperabilität

In einer modernen Enterprise-IT-Landschaft darf eine KI-Plattform keine isolierte Insel sein. Der wahre Wert künstlicher
Intelligenz entfaltet sich erst dann, wenn sie tief in die bestehenden Systeme, Datenquellen und Kommunikationskanäle
eines Unternehmens eingebettet ist. Datensilos und proprietäre Schnittstellen sind die grössten Feinde der digitalen
Transformation.

Der Swiss AI Hub begegnet dieser Herausforderung mit einer Strategie der radikalen Offenheit. Dieses Kapitel beschreibt,
wie sich die Plattform nahtlos in heterogene Umgebungen einfügt. Von der API-Kompatibilität, die eine Migration
bestehender Anwendungen in Minuten ermöglicht, bis hin zur nativen Präsenz in Microsoft Teams und Slack: Die Architektur
ist darauf ausgelegt, technische Hürden abzubauen und KI dort bereitzustellen, wo die Arbeit tatsächlich stattfindet.

## Auf einen Blick

- **API-First Strategie:** Eine vollständige OpenAI-Kompatibilität ermöglicht die sofortige Migration bestehender
  Anwendungen, während native APIs tiefen Zugriff auf Agenten-Workflows bieten.
- **Model Context Protocol (MCP):** Die Unterstützung des MCP-Standards erlaubt externen Entwicklungstools (wie Cursor
  oder Windsurf), den Plattform-Status direkt abzufragen und zu nutzen.
- **Bot-in-the-Loop:** Integration in Microsoft Teams und Slack ermöglicht nicht nur Chats, sondern auch die Eskalation
  von Agenten-Fragen an menschliche Experten direkt im Channel.
- **Echtzeit-Streaming:** WebSockets garantieren reaktive Benutzeroberflächen mit sofortigem Feedback und Einblick in
  den Denkprozess der KI.
- **Föderierte Identität:** Nahtloses Single Sign-On (SSO) via OIDC und OAuth 2.0 (z.B. Entra ID) ohne separate
  Passwortverwaltung.

## Standardisierte API-Architektur und Entwickler-Tools

### Geschäftlicher Nutzen

Für Unternehmen, die bereits erste Erfahrungen mit KI-Entwicklung gesammelt haben, stellt der Wechsel auf eine neue
Plattform oft ein Risiko dar. Investitionen in bestehenden Code, der auf den Schnittstellen von Marktführern wie OpenAI
basiert, drohen verloren zu gehen («Sunk Costs»). IT-Leiter benötigen die Sicherheit, dass eine Migration auf eine
souveräne Schweizer Plattform kein komplettes Neuschreiben der Applikationen erfordert. Gleichzeitig muss die
Schnittstelle zukunftssicher sein, um auch komplexe, proprietäre Agenten-Workflows und moderne Entwicklungsumgebungen
(IDEs) unterstützen zu können.

### Konzeptioneller Ansatz

Die Integrationsstrategie verfolgt einen hybriden API-Ansatz. Einerseits bietet die Plattform volle Kompatibilität zu
etablierten Industriestandards, um die Einstiegshürde so niedrig wie möglich zu halten. Das System verhält sich nach
aussen wie ein Standard-LLM-Provider, was den Austausch der Backend-Infrastruktur ohne Anpassung der Geschäftslogik
ermöglicht. Andererseits stehen erweiterte, plattformspezifische Schnittstellen bereit, um die volle Macht der
Agenten-Orchestrierung zu nutzen. Ein besonderer Fokus liegt auf der Unterstützung offener Protokolle für
Entwicklungswerkzeuge, um die Plattform transparent in den Coding-Workflow zu integrieren.

### Technische Umsetzung im Swiss AI Hub

Der Swiss AI Hub implementiert vier spezifische Schnittstellentypen auf Basis von FastAPI, um unterschiedliche
Integrationsbedürfnisse abzudecken:

- **OpenAI-kompatible REST-API:** Diese Schnittstelle spiegelt die Spezifikationen der OpenAI API exakt wider.
  Bestehende Anwendungen, die mit Standard-SDKs (Python oder Node.js) entwickelt wurden, müssen lediglich die Basis-URL
  und den API-Schlüssel ändern. Dies umfasst Chat Completions, Embeddings sowie Audioverarbeitung (Speech-to-Text).
- **Agenten-Interaktions-REST-API:** Für native Anwendungen bietet diese API tiefen Zugriff auf die Plattformlogik.
  Entwickler können hierüber Agenten-Workflows steuern, Prozesse starten und den Status von langlaufenden Aufgaben
  abfragen. Sie fungiert als Gateway zum internen NATS-Event-System.
- **WebSocket-API:** Um moderne, reaktive Benutzeroberflächen zu ermöglichen, unterstützt die Plattform bidirektionale
  Echtzeit-Kommunikation. Dies erlaubt das Streaming von Antworten («Token-by-Token») sowie die Übermittlung von
  Zwischenschritten («Thought Events»), sodass der Nutzer den Denkprozess des Agenten live verfolgen kann.
- **Model Context Protocol (MCP) Server:** Die Plattform implementiert den aufkommenden MCP-Standard. Der integrierte
  MCP-Server übersetzt FastAPI-Endpunkte automatisch in MCP-Ressourcen. Dies erlaubt es KI-gestützten
  Entwicklungsumgebungen (wie Claude Code oder JetBrains), die Fähigkeiten, verfügbaren Agenten und den Status des Swiss
  AI Hubs während der Entwicklung direkt abzufragen.

## Integration in Kommunikations- und Arbeitsplattformen

### Geschäftlicher Nutzen

Die Akzeptanz neuer Technologien scheitert oft daran, dass Mitarbeiter gezwungen werden, ihre gewohnten
Arbeitsumgebungen zu verlassen. Ein separates Webportal für KI-Anfragen erzeugt einen Medienbruch, der die Produktivität
senkt. Um dies zu vermeiden, muss die KI als virtueller Kollege dort präsent sein, wo die tägliche Kommunikation
stattfindet. Dies erhöht die Nutzungsrate drastisch und senkt den Schulungsaufwand. Zudem ermöglicht die Integration in
Kollaborationstools neuartige «Human-in-the-Loop»-Szenarien, bei denen die KI bei Unsicherheiten proaktiv Experten in
einem Chat-Kanal um Rat fragen kann.

### Konzeptioneller Ansatz

Anstatt für jeden Messenger eine eigene Integration zu bauen, setzt der Swiss AI Hub auf eine Abstraktionsschicht für
Konversationskanäle. Das Ziel ist eine «Write Once, Deploy Anywhere»-Strategie. Ein Agenten-Profil wird einmal
konfiguriert und kann anschliessend flexibel verschiedenen Kanälen zugewiesen werden. Die Plattform behandelt externe
Chat-Nachrichten technisch identisch zu internen API-Aufrufen, übersetzt jedoch die spezifischen Formate der
Drittanbieter (wie Adaptive Cards in Teams oder Block Kit in Slack) automatisch.

### Technische Umsetzung im Swiss AI Hub

Die technische Brücke bildet die Integration des **Azure Bot Service** in Kombination mit einer Ereignis-gesteuerten
Architektur via NATS.

- **Multichannel-Support:** Der Bot Service verbindet den Swiss AI Hub nativ mit Microsoft Teams, Slack und Outlook. Die
  Authentifizierung erfolgt dabei über die bestehende Azure AD (Entra ID) Infrastruktur des Unternehmens, sodass
  Sicherheitsrichtlinien gewahrt bleiben.
- **Bot-in-the-Loop:** Ein Alleinstellungsmerkmal ist die Fähigkeit von Agenten, ihre Ausführung zu pausieren und eine
  Frage in einen definierten Slack- oder Teams-Kanal zu posten (Experten-Eskalation). Antwortet ein menschlicher Experte
  im Thread, nimmt der Agent diese Information auf und setzt den Workflow fort. Dieser Zustand wird persistent in
  MongoDB oder Cosmos DB verwaltet, sodass auch bei längeren Wartezeiten kein Kontext verloren geht.
- **Streaming & Rich Media:** Auch in Teams und Slack werden Streaming-Antworten unterstützt, um Wartezeiten subjektiv
  zu verkürzen. Die Integration erlaubt zudem den Austausch von Dokumenten und Bildern, die direkt in die Daten-Pipeline
  des Agenten fliessen.

## Anbindung externer Fachsysteme und Prozessautomatisierung

### Geschäftlicher Nutzen

KI entfaltet ihren grössten Nutzen, wenn sie nicht nur redet, sondern handelt. Isolierte Chatbots können zwar Fragen
beantworten, aber keine Geschäftsprozesse auslösen. Unternehmen benötigen eine Plattform, die als intelligenter
Orchestrator fungiert und bestehende Fachanwendungen (ERP, CRM, Ticketsysteme) aktiv steuert. Dies ermöglicht einen
hohen Automatisierungsgrad, bei dem die KI Routineaufgaben übernimmt – wie das Auslesen einer Rechnung und das
anschliessende Verbuchen im SAP-System – und den Menschen von repetitiven Tätigkeiten entlastet.

### Konzeptioneller Ansatz

Die Interoperabilität mit Drittsystemen erfolgt bidirektional und richtet sich nach Latenz und Datenvolumen. Zum einen
können Agenten externe Systeme aktiv aufrufen («Outbound»), um Aktionen auszuführen. Zum anderen können externe Systeme
die KI als Dienst ansprechen («Inbound»), beispielsweise um bei Eingang eines neuen Dokuments automatisch eine
Klassifizierung zu triggern. Die Architektur vermeidet dabei starre Punkt-zu-Punkt-Verbindungen und setzt auf
standardisierte Protokolle.

### Technische Umsetzung im Swiss AI Hub

Der Swiss AI Hub unterscheidet vier etablierte Integrationsmuster:

- **Direkte Agenten-API-Aufrufe (Echtzeit/Outbound):** Innerhalb eines Agenten-Workflows können Python-Bibliotheken (wie
  `httpx`) genutzt werden, um REST-, SOAP- oder GraphQL-Schnittstellen externer Systeme anzusprechen. Dies ist ideal für
  synchrone Abfragen, etwa den Abruf eines Kundendatensatzes aus dem CRM während eines Chats.
- **Plattform-API-Integration (Echtzeit/Inbound):** Externe Systeme (z.B. ein Dokumentenmanagementsystem) rufen die
  Agenten-API auf, um KI-Analysen auszulösen. Der Traefik-Proxy regelt hierbei Rate-Limiting und Authentifizierung.
- **Daten-Pipelines (Batch/Inbound):** Für den Massendatenabgleich synchronisieren Dagster-Pipelines (siehe Kapitel 6)
  Daten aus Quellen wie SharePoint oder S3-Buckets in die Wissensdatenbank. Dies geschieht im Hintergrund, sodass die KI
  stets auf dem aktuellen Stand der Unternehmensdaten operiert.
- **Webhook-Integration:** Externe Automatisierungs-Tools (wie Power Automate, UiPath oder n8n) können als Event-Trigger
  fungieren, um asynchrone Prozesse zu starten und Ergebnisse entgegenzunehmen.

## Identitätsintegration und Single Sign-On (SSO)

### Geschäftlicher Nutzen

In der Enterprise-IT ist die Verwaltung von Benutzeridentitäten sicherheitskritisch. Eine KI-Plattform, die eine
separate Benutzerdatenbank mit eigenen Passwörtern erfordert, erhöht den administrativen Aufwand und das
Sicherheitsrisiko. CIOs und CISOs fordern eine nahtlose Einbindung in das zentrale Identity Access Management (IAM).
Mitarbeiter sollen sich mit ihren gewohnten Zugangsdaten anmelden können (Single Sign-On), und beim Austritt eines
Mitarbeiters muss der Zugriff auf die KI-Plattform automatisch entzogen werden.

### Konzeptioneller Ansatz

Der Swiss AI Hub speichert keine Passwörter. Die Architektur basiert auf dem Prinzip der föderierten Identität
(Federated Identity). Die Plattform delegiert den Authentifizierungsprozess vollständig an den vertrauenswürdigen
Identity Provider (IdP) des Unternehmens. Nach erfolgreicher Anmeldung erhält die Plattform lediglich ein signiertes
Token, das die Identität und die Gruppenzugehörigkeiten des Benutzers bestätigt. Dies ermöglicht eine zentrale Steuerung
von Zugriffsrichtlinien, wie etwa die Erzwingung von Multi-Faktor-Authentifizierung (MFA), direkt im IdP.

### Technische Umsetzung im Swiss AI Hub

Die technische Realisierung stützt sich auf die Industriestandards **OpenID Connect (OIDC)** und **OAuth 2.0**.

- **Standard-Konformität:** Die Plattform integriert sich out-of-the-box mit Microsoft Entra ID (ehemals Azure AD),
  Keycloak, Okta oder Zitadel.
- **Token-Validierung:** Bei jedem API-Aufruf validiert das System das übergebene JSON Web Token (JWT) kryptografisch
  (RSA-256) gegen den öffentlichen Schlüssel des IdP.
- **Automatisches Rollen-Mapping:** Benutzergruppen aus dem Verzeichnisdienst werden automatisch auf interne Rollen
  (z.B. *AgentVerwender-Rolle*) abgebildet. Dies geschieht durch Abfrage der Microsoft Graph API nach erfolgreicher
  Authentifizierung. Ein neuer Mitarbeiter hat somit ab dem ersten Tag Zugriff auf die relevanten Agenten, ohne dass ein
  Administrator im AI Hub tätig werden muss.
- **Service-Accounts:** Für technische Benutzer, beispielsweise für ETL-Prozesse, unterstützt die Plattform den OAuth
  2.0 Client Credentials Flow, um auch automatisierte Zugriffe sicher und auditierbar zu gestalten.
