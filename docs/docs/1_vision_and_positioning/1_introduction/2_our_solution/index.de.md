---
title: Unsere Lösung
source_sha: 37dd4fc99b0207324ecfa918bfb1ac61a6dd6949736cf593ed8f98cbe2af5f67
---

# Unsere Lösung: KI-Infrastruktur für Unternehmen als Produkt

Der Swiss AI Hub ist eine vollständige Open-Source-KI-Plattform, die Sie deployen, besitzen und kontrollieren. Es ist
kein Service, den Sie abonnieren, oder ein Framework, auf dem Sie aufbauen – es ist eine produktionsreife Infrastruktur,
die Ihnen gehört.

## Plattform + SDK: Das Komplettpaket

Der Swiss AI Hub besteht aus zwei komplementären Teilen:

**Die Plattform** ist Ihre KI-Infrastruktur. Sie ist unter Apache 2.0 lizenziert und umfasst alles, was für den Betrieb
von KI in der Produktion erforderlich ist: LLM Gateway, Vektordatenbanken, Daten-Pipelines, Authentifizierung,
Monitoring und Benutzeroberflächen. Deployen Sie sie mit `docker compose up` und Sie haben ein funktionierendes
KI-System.

**Das SDK** ist die Methode, wie Sie die Plattform erweitern. Es bietet die Muster, Tools und Frameworks zum Erstellen
von Agents, Pipelines und Prozessen, die sich automatisch in die Plattform integrieren. Wenn Sie mit unserem SDK
entwickeln, erben Ihre Komponenten alle Plattformfunktionen – sie benötigen kein kundenspezifisches Deployment,
Monitoring oder Benutzerzugriff, da die Plattform dies übernimmt.

## Was Sie sofort erhalten

Wenn Sie den Swiss AI Hub deployen, haben Sie sofort:

::: details Infrastrukturschicht
- **Einheitliches LLM Gateway** durch LiteLLM, das sich mit jedem Modell-Provider verbindet
- **Vektordatenbanken** (Milvus) für semantische Suche und RAG
- **Dokumentenverarbeitung** mit MinerU für PDFs, Office-Dateien und mehr
- **Daten-Pipelines** mit Dagster für Ingestion und Verarbeitung
- **Message Queuing** mit NATS für ereignisgesteuerte Architekturen
- **Objektspeicher** über eine S3-kompatible SeaweedFS-Schicht
- **Mehrere Datenbanken** (PostgreSQL, FerretDB, ValKey) vorkonfiguriert
:::

::: details KI-Funktionen
- **Multi-Provider LLM-Zugriff** mit automatischem Failover und Kostenverfolgung
- **Integriertes RAG** mit Dokumenten-Parsing, Chunking und Retrieval
- **Agent-Orchestrierung** für komplexe mehrstufige Workflows
- **Prozessautomatisierung** zur Koordination zwischen Menschen, KI und Systemen
- **PII-Erkennung und -Anonymisierung** durch Presidio
- **Embeddings und semantische Suche** mit konfigurierbaren Modellen
:::

::: details Enterprise-Funktionen
- **SSO/OAuth-Integration** mit Ihrem Identity Provider
- **Rollenbasierte Zugriffssteuerung** mit granularen Berechtigungen
- **Vollständige Audit Trails** für Compliance und Debugging
- **Kostenverfolgung und Limits** pro Benutzer, Team oder Modell
- **API-Tokens** für programmatischen Zugriff
- **Langfuse Tracing** für vollständige Observability
:::

::: details Benutzeroberflächen
- **Modernes Chat-Interface** mit Sprache, Bildern und Dokumenten
- **Prozess-Cockpit** für Workflow-Monitoring und -Beteiligung
- **Admin-Dashboard** für die Systemverwaltung
- **Microsoft Teams und Slack Bots** für Umgebungen, in denen Benutzer bereits arbeiten
- **OpenAI-kompatible API** für die Integration bestehender Tools
:::

## Wie es das Infrastrukturproblem löst

Erinnern Sie sich an die schwierigen Fragen von zuvor? Hier erfahren Sie, wie die Plattform diese beantwortet:

::: tip "Wie deployen wir das?"
Alles läuft in Containern. Ein Befehl startet den gesamten Stack. Skalieren Sie durch Anpassen der Container-Anzahl.
:::

::: tip "Wo bleiben unsere Daten?"
Dort, wo Sie es deployen. Betreiben Sie es On-Premise, in einem Schweizer Rechenzentrum oder in Ihrer bevorzugten Cloud.
Ihre Infrastruktur, Ihre Kontrolle.
:::

::: tip "Können wir verfolgen, was die KI tut?"
Jede Agent-Aktion wird durch Langfuse getraced. Jeder API-Aufruf wird geloggt. Jede Entscheidung ist auditierbar.
:::

::: tip "Wie kontrollieren wir die Kosten?"
LiteLLM bietet eine einheitliche Kostenverfolgung über alle Modelle hinweg. Legen Sie Limits pro Benutzer, Team oder
global fest.
:::

::: tip "Was passiert, wenn es fehlschlägt?"
Integrierte Fehlerbehandlung, automatisches Failover zwischen Modellen und anmutige Degradation zur menschlichen
Überprüfung.
:::

::: tip "Wie greifen Benutzer tatsächlich darauf zu?"
Über die Web-UI, Teams, Slack oder API. Die Authentifizierung wird von Ihrem bestehenden Identity Provider gehandhabt.
:::

::: tip "Können wir es in unsere bestehenden Tools integrieren?"
OpenAI-kompatible API für Tool-Kompatibilität. Ereignisgesteuerte Architektur für kundenspezifische Integrationen.
Webhook-Endpunkte für externe Systeme.
:::

## Warum Open Source alles verändert

Die Apache 2.0-Lizenz bedeutet, dass Sie keine Plattform adaptieren – Sie erwerben eine:

- **Kein Vendor Lock-in**: Der Code gehört Ihnen. Führen Sie ihn überall aus, ändern Sie ihn nach Bedarf
- **Keine Lizenzgebühren**: Zahlen Sie nur für die Infrastruktur, auf der Sie es betreiben
- **Transparente Operationen**: Jede Komponente ist inspizierbar und auditierbar
- **Community-getrieben**: Verbesserungen von anderen Organisationen kommen allen zugute
- **Zukunftssicher**: Würden wir morgen verschwinden, hätten Sie immer noch eine funktionierende Plattform

## Der SDK-Vorteil

Während die Plattform die Infrastrukturprobleme löst, reduziert das SDK die Entwicklungskomplexität. Das Bauen mit
unserem SDK bedeutet, dass Ihre Agents automatisch:

- Echtzeit-Updates an Benutzer über WebSocket-Verbindungen streamen
- Im Chat-Interface ohne kundenspezifische UI-Entwicklung erscheinen
- Ohne Instrumentierungscode getraced werden
- Authentifizierung und Autorisierung ohne Sicherheitslogik handhaben
- Zustand in bereitgestellten Datenbanken ohne Verbindungsmanagement speichern
- Dokumente durch bestehende Pipelines ohne kundenspezifisches Parsing verarbeiten

Sie schreiben die Geschäftslogik. Die Plattform erledigt den Rest.

## Ein praktisches Beispiel

So sieht das Deployment Ihrer ersten KI-Funktion aus:

1. **Klonen Sie das Repository** und konfigurieren Sie Umgebungsvariablen
2. **Führen Sie `docker compose up` aus**, um die Plattform zu starten
3. **Greifen Sie auf die Web-UI zu** und authentifizieren Sie sich mit Ihrem SSO
4. **Chatten Sie mit vorgefertigten Agents**, die sofort funktionieren
5. **Verbinden Sie Ihre Datenquellen** über das Admin-Interface
6. **Erstellen Sie bei Bedarf kundenspezifische Agents** mit SDK-Mustern

Keine Infrastruktur-Einrichtung. Keine Service-Bereitstellung. Keine komplexen Konfigurationen. Die Plattform ist vom
ersten Tag an produktionsbereit.

Dies ist Infrastruktur als Produkt: vollständig, funktional und bereit für Ihre Weiterentwicklung.
