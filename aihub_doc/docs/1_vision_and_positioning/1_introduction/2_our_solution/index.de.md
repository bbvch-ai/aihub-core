---
title: Unsere Lösung
source_sha: 1c41fc21fd964b11ddf51bfa8cc351ed71c0a4341251528d8f08487e153988f5
---

# Unsere Lösung: Enterprise-KI-Infrastruktur als Produkt

Der Swiss AI Hub ist eine vollständige Open-Source-KI-Plattform, die Sie deployen, besitzen und kontrollieren. Es ist
kein Dienst, den Sie abonnieren, oder ein Framework, auf dem Sie aufbauen – es ist eine produktionsreife Infrastruktur,
die Ihnen gehört.

## Plattform + SDK: Das Komplettpaket

Der Swiss AI Hub besteht aus zwei komplementären Teilen:

**Die Plattform** ist Ihre KI-Infrastruktur. Unter Apache 2.0 Lizenz enthält sie alles, was für den Betrieb von KI in
der Produktion benötigt wird: LLM-Gateway, Vektordatenbanken, Datenpipelines, Authentifizierung, Monitoring und
Benutzeroberflächen. Deployen Sie sie mit `docker compose up`, und Sie haben ein funktionierendes KI-System.

**Das SDK** ist die Art und Weise, wie Sie die Plattform erweitern. Es bietet die Muster, Tools und Frameworks für den
Aufbau von Agenten, Pipelines und Prozessen, die sich automatisch in die Plattform integrieren. Wenn Sie mit unserem SDK
entwickeln, erben Ihre Komponenten alle Plattformfunktionen – sie benötigen keine benutzerdefinierte Bereitstellung,
Überwachung oder Benutzerzugriff, da die Plattform dies übernimmt.

## Was Sie sofort erhalten

Wenn Sie den Swiss AI Hub deployen, haben Sie sofort:

::: details Infrastrukturschicht
- **Vereinheitlichtes LLM-Gateway** durch LiteLLM, das sich mit jedem Modell-Provider verbindet
- **Vektordatenbanken** (Milvus) für semantische Suche und RAG
- **Dokumentenverarbeitung** mit Docling für PDFs, Office-Dateien und mehr
- **Datenpipelines** mittels Dagster für Ingestion und Verarbeitung
- **Nachrichtenwarteschlange** mit NATS für ereignisgesteuerte Architektur
- **Objektspeicher** über die S3-kompatible Schicht von SeaweedFS
- **Mehrere Datenbanken** (PostgreSQL, FerretDB, ValKey) vorkonfiguriert
:::

::: details KI-Funktionen
- **Multi-Provider LLM-Zugriff** mit automatischem Failover und Kostenverfolgung
- **Integriertes RAG** mit Dokumenten-Parsing, Chunking und Retrieval
- **Agenten-Orchestrierung** für komplexe mehrstufige Workflows
- **Prozessautomatisierung** zur Koordination zwischen Menschen, KI und Systemen
- **PII-Erkennung und Anonymisierung** durch Presidio
- **Embeddings und semantische Suche** mit konfigurierbaren Modellen
:::

::: details Enterprise-Funktionen
- **SSO/OAuth-Integration** mit Ihrem Identitätsanbieter
- **Rollenbasierte Zugriffskontrolle** mit granularer Berechtigungsvergabe
- **Vollständige Audit-Trails** für Compliance und Debugging
- **Kostenverfolgung und Limits** pro Benutzer, Team oder Modell
- **API-Tokens** für den programmatischen Zugriff
- **Langfuse-Tracing** für vollständige Observability
:::

::: details Benutzeroberflächen
- **Modernes Chat-Interface** mit Sprach-, Bild- und Dokumentenunterstützung
- **Prozess-Cockpit** für Workflow-Überwachung und -Teilnahme
- **Admin-Dashboard** für die Systemverwaltung
- **Microsoft Teams und Slack Bots** für Umgebungen, in denen Benutzer bereits arbeiten
- **OpenAI-kompatible API** für die Integration bestehender Tools
:::

## Wie es das Infrastrukturproblem löst

Erinnern Sie sich an die schwierigen Fragen von zuvor? So beantwortet die Plattform sie:

::: tip „Wie deployen wir das?"
Alles läuft in Containern. Ein einziger Befehl startet den gesamten Stack. Skalieren Sie durch Anpassen der
Containeranzahl.
:::

::: tip „Wo bleiben unsere Daten?"
Wo auch immer Sie es deployen. Betreiben Sie es On-Premise, in einem Schweizer Rechenzentrum oder in Ihrer bevorzugten
Cloud. Ihre Infrastruktur, Ihre Kontrolle.
:::

::: tip „Können wir verfolgen, was die KI tut?"
Jede Agentenaktion wird durch Langfuse nachverfolgt. Jeder API-Aufruf wird protokolliert. Jede Entscheidung ist
auditierbar.
:::

::: tip „Wie kontrollieren wir die Kosten?"
LiteLLM bietet eine vereinheitlichte Kostenverfolgung über alle Modelle hinweg. Legen Sie Limits pro Benutzer, Team oder
global fest.
:::

::: tip „Was passiert, wenn es ausfällt?"
Integrierte Fehlerbehandlung, automatisches Failover zwischen Modellen und anmutige Degradation zur menschlichen
Überprüfung.
:::

::: tip „Wie greifen Benutzer tatsächlich darauf zu?"
Über die Web-UI, Teams, Slack oder API. Die Authentifizierung wird von Ihrem bestehenden Identitätsanbieter gehandhabt.
:::

::: tip „Können wir es in unsere bestehenden Tools integrieren?"
OpenAI-kompatible API für Tool-Kompatibilität. Ereignisgesteuerte Architektur für benutzerdefinierte Integrationen.
Webhook-Endpunkte für externe Systeme.
:::

## Warum Open Source alles verändert

Die Apache 2.0 Lizenz bedeutet, dass Sie keine Plattform einführen – Sie erwerben eine:

- **Kein Vendor Lock-in**: Der Code gehört Ihnen. Führen Sie ihn überall aus, modifizieren Sie ihn nach Bedarf.
- **Keine Lizenzgebühren**: Zahlen Sie nur für die Infrastruktur, auf der Sie ihn betreiben.
- **Transparente Operationen**: Jede Komponente ist überprüfbar und auditierbar.
- **Community-getrieben**: Verbesserungen von anderen Organisationen kommen allen zugute.
- **Zukunftssicher**: Wenn wir morgen verschwinden würden, hätten Sie immer noch eine funktionierende Plattform.

## Der SDK-Vorteil

Während die Plattform die Infrastrukturprobleme löst, reduziert das SDK die Entwicklungskomplexität. Wenn Sie mit
unserem SDK entwickeln, profitieren Ihre Agenten automatisch von folgenden Vorteilen:

- Echtzeit-Updates über WebSocket-Verbindungen an Benutzer streamen
- Ohne benutzerdefinierte UI-Entwicklung in der Chat-Oberfläche erscheinen
- Ohne Instrumentierungscode nachverfolgt werden
- Authentifizierung und Autorisierung ohne Sicherheitslogik handhaben
- Den Zustand in bereitgestellten Datenbanken ohne Verbindungsmanagement speichern
- Dokumente durch bestehende Pipelines ohne benutzerdefiniertes Parsing verarbeiten

Sie schreiben die Geschäftslogik. Die Plattform erledigt alles andere.

## Ein praktisches Beispiel

So sieht das Deployment Ihrer ersten KI-Funktion aus:

1. **Klonen Sie das Repository** und konfigurieren Sie Umgebungsvariablen
2. **Führen Sie `docker compose up` aus**, um die Plattform zu starten
3. **Greifen Sie auf die Web-UI zu** und authentifizieren Sie sich mit Ihrem SSO
4. **Chatten Sie mit vorgefertigten Agenten**, die sofort funktionieren
5. **Verbinden Sie Ihre Datenquellen** über die Admin-Oberfläche
6. **Erstellen Sie bei Bedarf benutzerdefinierte Agenten** mithilfe von SDK-Mustern

Keine Infrastruktur-Einrichtung. Keine Dienstbereitstellung. Keine komplexen Konfigurationen. Die Plattform ist vom
ersten Tag an produktionsbereit.

Dies ist Infrastruktur als Produkt: vollständig, funktionsfähig und bereit, von Ihnen erweitert zu werden.
