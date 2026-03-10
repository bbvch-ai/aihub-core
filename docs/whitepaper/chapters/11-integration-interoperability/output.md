# Kapitel 11: Integration und Interoperabilität

In einer modernen Enterprise-IT-Landschaft darf eine KI-Plattform keine isolierte Insel sein. Der wahre Wert künstlicher
Intelligenz entfaltet sich erst dann, wenn sie tief in die bestehenden Systeme, Datenquellen und Kommunikationskanäle
eines Unternehmens eingebettet ist. Datensilos und proprietäre Schnittstellen sind die grössten Feinde der digitalen
Transformation, da sie den Informationsfluss hemmen und die Komplexität unnötig erhöhen.

Der Swiss AI Hub begegnet dieser Herausforderung mit einer Strategie der radikalen Offenheit. Dieses Kapitel beschreibt,
wie sich die Plattform nahtlos in heterogene Umgebungen einfügt. Von der API-Kompatibilität, die eine Migration
bestehender Anwendungen in Minuten ermöglicht, bis hin zur nativen Präsenz in Microsoft Teams und Slack, ist die
Architektur darauf ausgelegt, technische Hürden abzubauen und KI dort bereitzustellen, wo die Arbeit tatsächlich
stattfindet.

## Auf einen Blick

- **API-First-Strategie:** Die vollständige OpenAI-Kompatibilität ermöglicht die sofortige Migration bestehender
  Anwendungen, während native APIs tiefen Zugriff auf komplexe Agenten-Workflows bieten.
- **Dynamische Endpunkt-Generierung:** Das System erstellt automatisch massgeschneiderte REST-Endpunkte für neu
  bereitgestellte Agenten und Prozesse, was manuelle API-Entwicklung überflüssig macht.
- **Multichannel-Kollaboration:** Durch den Azure Bot Service wird KI direkt in Microsoft Teams, Slack und Outlook
  integriert, einschliesslich der Fähigkeit zur Eskalation an menschliche Experten via Bot-in-the-Loop.
- **Model Context Protocol (MCP):** Die Unterstützung des MCP-Standards erlaubt es KI-Entwicklungstools, den
  Plattform-Status direkt abzufragen und Agenten während der Entwicklung zu inspizieren.
- **Föderierte Identität:** Ein nahtloses Single Sign-On (SSO) über Industriestandards wie OIDC und OAuth 2.0 garantiert
  die Einhaltung zentraler Sicherheitsrichtlinien ohne zusätzliche Passwortverwaltung.

## Standardisierte API-Architektur und Entwickler-Schnittstellen

### Geschäftlicher Nutzen

Für Unternehmen, die bereits erste Erfahrungen mit KI-Entwicklung gesammelt haben, stellt der Wechsel auf eine neue
Plattform oft ein erhebliches Risiko dar. Investitionen in bestehenden Code, der auf den Schnittstellen von globalen
Marktführern basiert, drohen verloren zu gehen, was die Modernisierung der Infrastruktur bremst. IT-Leiter benötigen die
Sicherheit, dass eine Migration auf eine souveräne Schweizer Plattform kein komplettes Neuschreiben der Applikationen
erfordert. Gleichzeitig muss die Schnittstellenlandschaft flexibel genug sein, um sowohl einfache Chat-Anfragen als auch
hochkomplexe, ereignisgesteuerte Geschäftsprozesse abzubilden, ohne neue Flaschenhälse in der Entwicklung zu erzeugen.

### Konzeptioneller Ansatz

Die Integrationsstrategie verfolgt einen hybriden API-Ansatz, der Standardisierung mit nativer Leistungsfähigkeit
kombiniert. Einerseits bietet die Plattform volle Kompatibilität zu etablierten Industriestandards, um die
Einstiegshürde so niedrig wie möglich zu halten. Das System verhält sich nach aussen wie ein Standard-LLM-Provider, was
den Austausch der Backend-Infrastruktur ohne Anpassung der Geschäftslogik ermöglicht. Andererseits stehen erweiterte,
plattformspezifische Schnittstellen bereit, um die volle Macht der Agenten-Orchestrierung zu nutzen. Ein besonderer
Schwerpunkt liegt auf der Automatisierung: Anstatt APIs manuell zu definieren, erkennt die Plattform neue Fähigkeiten
selbstständig und stellt diese programmatisch bereit.

### Technische Umsetzung im Swiss AI Hub

Der Swiss AI Hub implementiert vier spezifische Schnittstellentypen auf Basis von FastAPI, um unterschiedliche
Integrationsbedürfnisse abzudecken. Die OpenAI-kompatible REST-API spiegelt die Spezifikationen der OpenAI-API exakt
wider, sodass Anwendungen, die mit Standard-SDKs entwickelt wurden, lediglich die Basis-URL und den API-Schlüssel ändern
müssen. Dies umfasst Chat Completions, Embeddings sowie die Audioverarbeitung. Für native Anwendungen bietet die
Agenten-Interaktions-REST-API tiefen Zugriff auf die Plattformlogik, wodurch Entwickler Agenten-Workflows steuern, den
Status langlaufender Aufgaben abfragen und auf den Ereignisverlauf zugreifen können.

Ein technologisches Highlight sind die dynamischen Agenten- und Prozess-Endpunkte. Ein Discovery-Dienst scannt
kontinuierlich das interne NATS-System nach verfügbaren Komponenten und generiert automatisch typisierte REST-Endpunkte
basierend auf deren Ereignisspezifikationen. Ergänzt wird dies durch die WebSocket-API für bidirektionale
Echtzeit-Kommunikation, die das Streaming von Antworten sowie die Übermittlung von Zwischenschritten («Thought Events»)
erlaubt. Schliesslich implementiert der Swiss AI Hub einen Model Context Protocol (MCP) Server, der die
plattforminternen Ressourcen für KI-gestützte Entwicklungsumgebungen wie Cursor oder Claude Code zugänglich macht, was
die Entwicklerproduktivität massiv steigert.

## Integration in Kommunikations- und Arbeitsplattformen

### Geschäftlicher Nutzen

Die Akzeptanz neuer Technologien scheitert in der Praxis oft daran, dass Mitarbeitende gezwungen werden, ihre gewohnten
Arbeitsumgebungen zu verlassen. Ein separates Webportal für KI-Anfragen erzeugt einen Medienbruch, der die tägliche
Produktivität senkt und die Hemmschwelle zur Nutzung erhöht. Um dies zu vermeiden, muss die KI als virtueller Kollege
dort präsent sein, wo die tägliche Kommunikation stattfindet. Dies steigert die Nutzungsrate nachweislich und senkt den
Schulungsaufwand erheblich. Zudem ermöglicht die tiefe Integration in Kollaborationstools neuartige Szenarien der
Zusammenarbeit, bei denen die KI bei Unsicherheiten proaktiv Experten um Rat fragen kann, ohne den digitalen Raum zu
wechseln.

### Konzeptioneller Ansatz

Anstatt für jeden Messenger eine isolierte Integration zu entwickeln, setzt der Swiss AI Hub auf eine
Abstraktionsschicht für Konversationskanäle. Das Ziel ist eine «Write Once, Deploy Anywhere»-Strategie, bei der ein
Agenten-Profil einmal konfiguriert und anschliessend flexibel verschiedenen Kanälen zugewiesen wird. Die Plattform
behandelt externe Chat-Nachrichten technisch identisch zu internen API-Aufrufen, übersetzt jedoch die spezifischen
Formate der Drittanbieter automatisch. Ein zentraler Bestandteil dieses Konzepts ist das Bot-in-the-Loop-Muster, welches
die Lücke zwischen autonomer KI-Verarbeitung und menschlicher Expertise schliesst, indem es Arbeitsschritte an
kritischen Entscheidungspunkten unterbricht.

### Technische Umsetzung im Swiss AI Hub

Die technische Brücke bildet die Integration des Azure Bot Service in Kombination mit einer ereignisgesteuerten
Architektur via NATS. Dieser Dienst verbindet den Swiss AI Hub nativ mit Microsoft Teams, Slack, Outlook und weiteren
Kanälen wie Skype oder Web-Chat-Widgets. Die Authentifizierung erfolgt dabei über die bestehende Identitätsinfrastruktur
des Unternehmens, wodurch Sicherheitsrichtlinien gewahrt bleiben. Ein Alleinstellungsmerkmal ist die
Bot-in-the-Loop-Infrastruktur: Ein Agent kann seine Ausführung pausieren und eine strukturierte Frage in einen
definierten Slack- oder Teams-Kanal posten.

Sobald ein menschlicher Experte im entsprechenden Thread antwortet, erfasst das System diese Information als Ereignis,
nimmt den Kontext wieder auf und setzt den Workflow des Agenten automatisch fort. Dieser Zustand wird persistent in der
Datenbank verwaltet, sodass auch bei längeren Wartezeiten kein Wissen verloren geht. Die Integration unterstützt zudem
Rich Media, einschliesslich des Austauschs von Dokumenten und Bildern, die direkt in die Daten-zu-Wissen-Pipeline des
Agenten fliessen. Für eine natürliche Nutzererfahrung werden Echtzeit-Tipp-Indikatoren und inkrementelle
Streaming-Antworten über alle Kanäle hinweg unterstützt.

## Anbindung externer Fachsysteme und Prozessautomatisierung

### Geschäftlicher Nutzen

Künstliche Intelligenz entfaltet ihren grössten geschäftlichen Nutzen, wenn sie nicht nur Informationen liefert, sondern
aktiv handelt. Isolierte Chatbots können zwar Fragen beantworten, aber keine komplexen Geschäftsprozesse auslösen.
Unternehmen benötigen eine Plattform, die als intelligenter Orchestrator fungiert und bestehende Fachanwendungen wie
ERP-, CRM- oder Ticketsysteme aktiv steuert. Dies ermöglicht einen hohen Automatisierungsgrad, bei dem die KI
Routineaufgaben übernimmt, wie das Auslesen einer Rechnung und das anschliessende Verbuchen in einem System, und so die
Mitarbeitenden von repetitiven Tätigkeiten entlastet.

### Konzeptioneller Ansatz

Die Interoperabilität mit Drittsystemen erfolgt bidirektional und richtet sich nach den Anforderungen an Latenz und
Datenvolumen. Zum einen können Agenten externe Systeme aktiv aufrufen, um Aktionen auszuführen oder Daten abzufragen.
Zum anderen können externe Systeme die KI als spezialisierten Dienst ansprechen, beispielsweise um bei Eingang eines
neuen Dokuments automatisch eine Klassifizierung oder Zusammenfassung zu triggern. Die Architektur vermeidet dabei
starre Punkt-zu-Punkt-Verbindungen und setzt auf standardisierte Protokolle sowie eine ereignisgesteuerte Kommunikation,
die sicherstellt, dass Systeme entkoppelt bleiben und unabhängig voneinander skalieren können.

### Technische Umsetzung im Swiss AI Hub

Der Swiss AI Hub stellt für diese Anforderungen vier etablierte Integrationsmuster bereit:

- **Direkte Agenten-API-Aufrufe:** Innerhalb eines Agenten-Workflows können Standard-Bibliotheken genutzt werden, um
  REST-, SOAP- oder GraphQL-Schnittstellen externer Systeme in Echtzeit anzusprechen. Dies ist ideal für den Abruf von
  Kundendaten während einer Interaktion.
- **Plattform-API-Integration:** Externe Fachanwendungen rufen die Agenten-Interaktions-API auf, um KI-Analysen
  auszulösen. Der Traefik-Proxy regelt hierbei die Authentifizierung und das Rate-Limiting zum Schutz der Infrastruktur.
- **Daten-zu-Wissen-Pipelines:** Für den Massendatenabgleich synchronisieren Dagster-Pipelines kontinuierlich Daten aus
  Quellen wie SharePoint, Confluence oder S3-Buckets in die Wissensdatenbank. Diese Batch-Synchronisierung stellt
  sicher, dass die KI stets auf dem aktuellen Stand der Unternehmensdaten operiert.
- **Webhook-Integration:** Die Plattform lässt sich über Webhooks als intelligente Komponente in übergeordnete
  Automatisierungswerkzeuge wie Microsoft Power Automate, n8n oder UiPath integrieren, um systemübergreifende Workflows
  effizient zu steuern.

## Identitätsintegration und Single Sign-On (SSO)

### Geschäftlicher Nutzen

In der Enterprise-IT ist die Verwaltung von Benutzeridentitäten ein sicherheitskritischer Aspekt der Governance. Eine
KI-Plattform, die eine separate Benutzerdatenbank mit eigenen Passwörtern erfordert, erhöht nicht nur den
administrativen Aufwand, sondern schafft auch zusätzliche Sicherheitsrisiken und senkt die Benutzerakzeptanz.
Organisationen fordern eine nahtlose Einbindung in das zentrale Identity and Access Management (IAM). Mitarbeitende
sollen sich mit ihren gewohnten Zugangsdaten anmelden können, während die IT sicherstellen muss, dass beim Austritt
eines Mitarbeitenden der Zugriff auf alle KI-Ressourcen automatisch und ohne Verzug entzogen wird.

### Konzeptioneller Ansatz

Der Swiss AI Hub speichert konsequent keine Passwörter, sondern basiert auf dem Prinzip der föderierten Identität. Die
Plattform delegiert den gesamten Authentifizierungsprozess an den vertrauenswürdigen Identity Provider (IdP) des
Unternehmens. Nach der erfolgreichen Anmeldung erhält die Plattform ein kryptografisch signiertes Token, das die
Identität und die Gruppenzugehörigkeiten des Benutzers bestätigt. Dies ermöglicht eine zentrale Steuerung von
Sicherheitsrichtlinien, wie die Erzwingung von Multi-Faktor-Authentifizierung (MFA), direkt im IdP. Das
Berechtigungssystem der Plattform nutzt diese Informationen, um den Zugriff auf spezifische Agenten-Profile und
Wissensdatenbanken dynamisch zu steuern.

### Technische Umsetzung im Swiss AI Hub

Die technische Realisierung stützt sich auf die Industriestandards OpenID Connect (OIDC) und OAuth 2.0. Die Plattform
integriert sich out-of-the-box mit Microsoft Entra ID (ehemals Azure AD), Keycloak, Okta oder ZITADEL. Bei jedem
API-Aufruf validiert das System das übergebene JSON Web Token (JWT) mittels RSA-256 gegen den öffentlichen Schlüssel des
Identity Providers.

Ein besonderes Merkmal ist das automatische Rollen-Mapping: Benutzergruppen aus dem Verzeichnisdienst werden über die
Microsoft Graph API abgefragt und direkt auf interne Rollen, wie etwa die AgentVerwender-Rolle oder die
WissensVerwalter-Rolle, abgebildet. Dadurch erhält ein neuer Mitarbeitender ab dem ersten Tag automatisch Zugriff auf
die für seine Abteilung relevanten Agenten, ohne dass ein Administrator manuell eingreifen muss. Für automatisierte
Prozesse unterstützt die Plattform zudem den OAuth 2.0 Client Credentials Flow, wodurch auch technische Benutzer sicher
und auditierbar auf die KI-Dienste zugreifen können.
