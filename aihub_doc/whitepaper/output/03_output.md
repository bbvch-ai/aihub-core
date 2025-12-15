# Datensouveränität und vollständige Kundenkontrolle

Die Einführung von künstlicher Intelligenz in Schweizer Unternehmen und Behörden scheitert oft nicht an der technischen
Machbarkeit, sondern an der Frage der Datenhoheit. Wer kontrolliert die Informationen, wenn sie in Vektoren umgewandelt
werden? Wo werden die Eingabeaufforderungen (Prompts) verarbeitet? Und wie wird verhindert, dass strategisches Wissen in
den undurchsichtigen Trainingsdaten globaler KI-Modelle aufgeht?

Der Swiss AI Hub adressiert diese Risiken durch ein Architekturdesign, das auf dem Prinzip der strikten
Datensouveränität basiert. Dieses Kapitel legt dar, wie Organisationen die volle Kontrolle über Speicherort,
Zugriffsrechte und Informationsflüsse behalten, unabhängig davon, ob die Plattform im eigenen Rechenzentrum oder in
einer Private Cloud betrieben wird.

## Auf einen Blick

- **Garantierte Datenresidenz:** Durch «Bring Your Own Infrastructure» verbleiben sämtliche persistierten Daten physisch
  im Sicherheitsperimeter des Mandanten.
- **Security by Invisibility:** Ein dynamisches Berechtigungssystem blendet nicht autorisierte Funktionen und Daten in
  der Benutzeroberfläche vollständig aus.
- **Modell-Agnostik:** Ein integriertes LLM-Gateway ermöglicht den freien Wechsel zwischen Cloud-Modellen und lokal
  betriebenen Open-Source-LLMs.
- **Deep Observability:** Vollständige Transparenz aller KI-Entscheidungen durch OpenTelemetry-Standards, ohne
  Datenhoheit an Monitoring-Anbieter abzugeben.
- **Compliance-Automatisierung:** Integrierte Mechanismen für PII-Maskierung und automatische Löschzyklen unterstützen
  die Einhaltung von revDSG und DSGVO.

## Physische Datenkontrolle und Deployment-Flexibilität

### Geschäftlicher Nutzen

Für regulierte Industrien, das Gesundheitswesen und die öffentliche Verwaltung ist der physische Standort der Daten
nicht verhandelbar. Die Nutzung öffentlicher SaaS-Angebote scheidet oft aus, da die Datenhoheit faktisch an den Anbieter
abgetreten wird. Organisationen benötigen die Gewissheit, dass sensible Unternehmensdaten den definierten Rechtsraum –
typischerweise die Schweiz – niemals verlassen. Gleichzeitig darf diese Sicherheit nicht zu Lasten der Modernität gehen;
die IT-Abteilung benötigt eine Lösung, die sich nahtlos in bestehende Infrastrukturen integriert, sei es in einem
Hochsicherheits-Rechenzentrum oder einer verwalteten Schweizer Cloud-Umgebung.

### Konzeptioneller Ansatz

Der Swiss AI Hub verfolgt den Ansatz «Bring Your Own Infrastructure». Die Plattform wird als containerisierte
Software-Lösung bereitgestellt, die vollständig innerhalb der Umgebung des Mandanten läuft. Es existieren keine
«Phone-Home»-Funktionen, die Nutzdaten an den Hersteller senden.

Die Architektur unterstützt differenzierte Betriebsmodelle:

1. **Einzelinstanz-Deployment:** Eine vollständig isolierte Installation für eine Organisation, bei der Datenbanken und
   Dienste dediziert betrieben werden.
2. **Multi-Instanz-Deployment:** Für Szenarien mit höchsten Sicherheitsanforderungen (z.B. Trennung zwischen
   Versicherung und medizinischem Dienst) werden physisch getrennte Instanzen betrieben («Shared Nothing Architecture»).
   Datenlecks zwischen diesen Instanzen sind technisch ausgeschlossen, selbst bei Fehlkonfigurationen auf
   Anwendungsebene.
3. **Air-Gapped:** Die Plattform kann komplett ohne Internetverbindung betrieben werden, wobei lokale KI-Modelle die
   externe Kommunikation ersetzen.

### Technische Umsetzung im Swiss AI Hub

Die Bereitstellung erfolgt als Set von Docker-Containern, orchestriert via Docker Compose oder Kubernetes. Die
Datenhaltung ist strikt lokalisiert: Relationale Daten liegen in **PostgreSQL** (via FerretDB), Vektoreinbettungen in
**Milvus** oder Azure AI Search, und Dokumente in S3-kompatiblen Speichern wie SeaweedFS oder Azure Data Lake.

In einem Multi-Instanz-Szenario agieren die Instanzen vollständig autark. Die einzige Komponente, die optional geteilt
werden kann, ist das LLM-Backend (z.B. eine dedizierte Azure OpenAI Instanz oder ein GPU-Cluster mit vLLM). Da das
vorgeschaltete **LLM-Gateway** (LiteLLM) jedoch zustandslos arbeitet und keine Prompts oder Antworten persistiert,
bleibt die Datenisolation gewahrt. Die Kommunikation zwischen den internen Diensten und dem Gateway ist standardmässig
via TLS verschlüsselt.

## Granulare Zugriffskontrolle und dynamische Sichtbarkeit

### Geschäftlicher Nutzen

Datensouveränität bedeutet nicht nur den Schutz vor externen Zugriffen, sondern auch die Kontrolle der internen
Informationsflüsse. Ein häufiges Hindernis für den breiten KI-Einsatz ist die Sorge, dass sensible HR-Dokumente oder
Management-Entscheidungen durch eine KI-Suche für unberechtigte Mitarbeiter sichtbar werden. C-Level-Verantwortliche und
Compliance-Beauftragte benötigen die Garantie, dass das Prinzip der minimalen Rechtevergabe (Least Privilege) auch in
der Ära generativer KI durchgesetzt wird und Benutzer nur Zugriff auf Funktionen erhalten, die ihrer Rolle entsprechen.

### Konzeptioneller Ansatz

Der Swiss AI Hub implementiert ein fortschrittliches Sicherheitsmodell, das als «Security by Invisibility» bezeichnet
wird. Anstatt Benutzern inaktive Schaltflächen oder Fehlermeldungen zu präsentieren, passt sich die Benutzeroberfläche
dynamisch an die Berechtigungen an.

Das System unterscheidet hierbei zwischen **Multi-Instancing** (physische Trennung) und **Multi-Tenancy** (logische
Trennung innerhalb einer Instanz). Innerhalb eines Mandanten regelt die rollenbasierte Zugriffskontrolle (RBAC) den
Zugriff auf Ressourcen. Ein Benutzer sieht in der Benutzeroberfläche schlichtweg keine Dienste, Agenten-Profile oder
Wissensdatenbanken, für die er keine explizite Berechtigung besitzt. Dies reduziert die Angriffsfläche drastisch, da
Benutzer nicht versuchen können, auf Dienste zuzugreifen, deren Existenz ihnen verborgen bleibt.

### Technische Umsetzung im Swiss AI Hub

Das Berechtigungssystem basiert auf einer hierarchischen Punkt-Notation, die eine extrem feingranulare Steuerung
erlaubt.

- **Hierarchische Berechtigungen:** Rechte werden im Format `aihub.user.agent.<agent_class>.<agent_id>` vergeben. Dies
  ermöglicht präzise Regeln wie `aihub.user.agent.hr_support.instance_001` für Zugriff auf einen spezifischen Agenten
  oder `aihub.user.agent.hr_support.*` für alle Instanzen einer Klasse.
- **Backend-Evaluierung:** Die Prüfung erfolgt ausschliesslich im Backend durch einen zentralen «Access Checker». Das
  Frontend erhält lediglich einen gefilterten Dienstkatalog. Manipulationen im Client sind dadurch wirkungslos.
- **Dynamische Wildcards:** Administratoren können mächtige Wildcards wie `>` (alle verbleibenden Segmente) oder `?*`
  (Existenzprüfung) nutzen, um komplexe Organisationsstrukturen abzubilden, ohne jede Ressource einzeln berechtigen zu
  müssen.
- **Identitätsintegration:** Die Authentifizierung erfolgt über OIDC/OAuth2, was die Synchronisation von Rollen aus
  bestehenden Systemen wie Azure AD oder Keycloak ermöglicht. Änderungen an Rollen werden ohne Neuanmeldung sofort
  wirksam.

## Unabhängigkeit von Modell-Anbietern und PII-Schutz

### Geschäftlicher Nutzen

Die Abhängigkeit von einzelnen US-Hyperscalern stellt ein strategisches Klumpenrisiko dar. Preisänderungen, Anpassungen
der Nutzungsbedingungen oder geopolitische Spannungen können die Verfügbarkeit kritischer KI-Funktionen gefährden. Zudem
ist das unmaskierte Senden von personenbezogenen Daten (PII) an externe APIs oft ein Verstoss gegen Datenschutzgesetze
wie das revDSG oder die DSGVO. Organisationen benötigen eine Architektur, die Modell-Agnostik garantiert und als
Schutzschild vor den externen KI-Diensten fungiert.

### Konzeptioneller Ansatz

Der Swiss AI Hub fungiert als intelligenter Mediator zwischen der Unternehmensanwendung und den KI-Modellen. Die
Plattform abstrahiert die spezifischen APIs der Anbieter hinter einer einheitlichen Schnittstelle. Das bedeutet, dass
die Organisation frei entscheiden kann, welche Anfrage von welchem Modell verarbeitet wird.

Für den Datenschutz gilt das Konzept der **Datenanonymisierung an der Quelle**. Bevor eine Anfrage das kontrollierte
Netzwerk verlässt, muss sie bereinigt werden. Sensible Daten werden entweder maskiert oder die Anfrage wird komplett
blockiert, um Datenabfluss zu verhindern.

### Technische Umsetzung im Swiss AI Hub

Zentrales Element ist das **LLM-Gateway** (implementiert durch LiteLLM). Es bietet eine OpenAI-kompatible Schnittstelle
für alle Modelle – egal ob Azure OpenAI, Google Gemini, Anthropic oder lokale Open-Source-Modelle.

- **PII-Schutz mit Presidio:** Die Integration von **Presidio** ermöglicht das Scannen von Prompts auf Muster wie
  E-Mail-Adressen, Kreditkartennummern oder Namen. Administratoren können konfigurieren, ob diese Daten maskiert
  (Ersetzen durch `[PERSON]`) oder die Anfrage im «Blockierungsmodus» komplett abgewiesen wird.
- **Lokale Inferenz:** Für maximale Unabhängigkeit unterstützt die Plattform das Hosting eigener Modelle mittels vLLM,
  llama.cpp oder Hugging Face Text Embedding Inference. Dies ermöglicht den Betrieb in Air-Gapped-Umgebungen, da keine
  Daten das eigene Rechenzentrum verlassen müssen.
- **Routing-Kontrolle:** Über die Konfiguration kann festgelegt werden, dass hochsensible Agenten-Profile zwingend
  lokale Modelle nutzen, während allgemeine Aufgaben an leistungsfähigere Cloud-Modelle routen.

## Langzeit-Verfügbarkeit, Compliance und Deep Observability

### Geschäftlicher Nutzen

Investitionen in KI-Infrastruktur müssen langfristig gesichert und auditierbar sein. Ein häufiges Risiko bei
proprietären KI-Lösungen ist der Vendor-Lock-in bei Monitoring- und Audit-Daten. Entscheidungsträger müssen
sicherstellen, dass sie jederzeit nachweisen können, warum eine KI eine bestimmte Entscheidung getroffen hat, ohne dabei
sensible Log-Daten an externe SaaS-Monitoring-Tools senden zu müssen. Zudem verlangen Gesetze wie die DSGVO Mechanismen
für das «Recht auf Vergessenwerden».

### Konzeptioneller Ansatz

Die Strategie basiert auf Offenheit und Standards. Die Plattform nutzt **OpenTelemetry (OTel)** als Fundament für
Observability. Dies garantiert, dass Telemetriedaten (Metriken, Logs, Traces) dem Kunden gehören und in beliebige
Backends exportiert werden können. Compliance ist kein nachträglicher Gedanke, sondern technisch verankert: Ephemere
Daten haben automatische Verfallsdaten, und Löschkonzepte sind tief in der Datenhaltung integriert.

### Technische Umsetzung im Swiss AI Hub

- **Deep Observability:** Die Plattform implementiert Distributed Tracing über alle Komponenten hinweg (Agenten,
  LLM-Aufrufe, Datenbanken). KI-spezifische Operationen nutzen «OpenInference Semantic Conventions», um Details wie
  Token-Verbrauch und abgerufene Dokumente sichtbar zu machen.
- **Duale Tracing-Pipelines:** Der OpenTelemetry Collector trennt Datenströme intelligent. Die Pipeline `traces/phoenix`
  liefert detaillierte KI-Traces für die lokale Entwicklung und Analyse an **Phoenix**, während `traces/cloud`
  gefilterte operative Daten an Langzeitspeicher wie SigNoz, Datadog oder Dynatrace sendet.
- **Compliance-Automation:** Ephemere Daten werden standardmässig nach 30 Tagen automatisch gelöscht. Das System
  unterstützt die gezielte Löschung von Benutzerdaten (Right to be Forgotten) und bietet unveränderliche Audit-Logs für
  regulatorische Nachweise. Da Vektordaten in offenen Formaten liegen, ist ein Datenexport jederzeit ohne
  Hersteller-Tools möglich.
