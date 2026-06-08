---
title: Unsere Lösung
source_sha: c0c87f92d15751937b85f4cb85455d0f6ef67bb20c21f6e499ccdf1adea8b095
---

# Unsere Lösung: Enterprise AI-Infrastruktur als Produkt

Der Swiss AI Hub ist eine komplette Open-Source-KI-Plattform, die Sie deployen, besitzen und kontrollieren. Es ist kein
Service, den Sie abonnieren, oder ein Framework, auf dem Sie aufbauen – es ist eine produktionsreife Infrastruktur, die
Ihnen gehört.

## Plattform + SDK: Das Komplettpaket

Der Swiss AI Hub besteht aus zwei komplementären Teilen:

**Die Plattform** ist Ihre KI-Infrastruktur. Open-Source (Apache 2.0 für die Runtime + SDK, AGPL-3.0 für die
Benutzeroberfläche und Backup-Orchestrierung; siehe
[LICENSES.md](https://github.com/bbvch-ai/aihub-core/blob/main/LICENSES.md) für die Aufschlüsselung pro Paket), umfasst
sie alles, was zum Betrieb von KI in der Produktion benötigt wird: LLM Gateway, Vektordatenbanken, Data Pipelines,
Authentifizierung, Monitoring und Benutzeroberflächen. Deployen Sie sie mit `docker compose up` und Sie haben ein
funktionierendes KI-System.

**Das SDK** ist die Art und Weise, wie Sie die Plattform erweitern. Es bietet die Muster, Tools und Frameworks zum
Erstellen von Agents, Pipelines und Prozessen, die sich automatisch in die Plattform integrieren. Wenn Sie mit unserem
SDK entwickeln, erben Ihre Komponenten alle Plattformfunktionen – sie benötigen kein benutzerdefiniertes Deployment,
Monitoring oder Benutzerzugriff, da die Plattform dies übernimmt.

## Was Sie Out-of-the-Box erhalten

Wenn Sie den Swiss AI Hub deployen, haben Sie sofort:

::: details Infrastrukturebene
- **Vereinheitlichtes LLM-Gateway** über LiteLLM, das sich mit jedem Modell-Provider verbindet
- **Vektordatenbanken** (Milvus) für semantische Suche und RAG (Retrieval-Augmented Generation)
- **Dokumentenverarbeitung** mit MinerU für PDFs, Office-Dateien und mehr
- **Data Pipelines** mit Dagster für Ingestion und Verarbeitung
- **Message Queuing** mit NATS für ereignisgesteuerte Architektur
- **Objektspeicher** über die S3-kompatible Schicht von SeaweedFS
- **Mehrere Datenbanken** (PostgreSQL, FerretDB, ValKey) vorkonfiguriert
:::

::: details KI-Funktionen
- **Multi-Provider LLM-Zugriff** mit automatischem Failover und Kostenverfolgung
- **Integriertes RAG** mit Dokumenten-Parsing, Chunking und Retrieval
- **Agent-Orchestrierung** für komplexe Multi-Step Workflows
- **Prozessautomatisierung**, die zwischen Menschen, KI und Systemen koordiniert
- **PII-Erkennung und Anonymisierung** durch Presidio
- **Embeddings und semantische Suche** mit konfigurierbaren Modellen
:::

::: details Enterprise-Funktionen
- **SSO/OAuth-Integration** mit Ihrem Identity Provider
- **Rollenbasierte Zugriffskontrolle** mit granularen Berechtigungen
- **Vollständige Audit Trails** für Compliance und Debugging
- **Kostenverfolgung und Limits** pro Benutzer, Team oder Modell
- **API-Tokens** für programmatischen Zugriff
- **Langfuse Tracing** für vollständige Observability
:::

::: details Benutzeroberflächen
- **Moderne Chat-Benutzeroberfläche** mit Sprach-, Bild- und Dokumentenunterstützung
- **Prozess-Cockpit** für Workflow-Monitoring und -Teilnahme
- **Admin-Dashboard** für die Systemverwaltung
- **Microsoft Teams- und Slack-Bots** für die Arbeitsumgebung, in der Benutzer bereits tätig sind
- **OpenAI-kompatible API** für die Integration bestehender Tools
:::

## Wie es das Infrastrukturproblem löst

Erinnern Sie sich an die schwierigen Fragen von zuvor? So beantwortet die Plattform sie:

::: tip "Wie deployen wir das?"
Alles läuft in Containern. Ein Befehl startet den gesamten Stack. Skalieren Sie durch Anpassen der Container-Anzahl.
:::

::: tip "Wo bleiben unsere Daten?"
Wo immer Sie es deployen. Betreiben Sie es On-Premise, in einem Schweizer Rechenzentrum oder Ihrer bevorzugten Cloud.
Ihre Infrastruktur, Ihre Kontrolle.
:::

::: tip "Können wir verfolgen, was die KI tut?"
Jede Agent-Aktion wird über Langfuse getraced. Jeder API-Aufruf wird geloggt. Jede Entscheidung ist auditierbar.
:::

::: tip "Wie kontrollieren wir die Kosten?"
LiteLLM bietet eine vereinheitlichte Kostenverfolgung über alle Modelle hinweg. Legen Sie Limits pro Benutzer, Team oder
global fest.
:::

::: tip "Was passiert, wenn es fehlschlägt?"
Integrierte Fehlerbehandlung, automatisches Failover zwischen Modellen und graceful Degradation zur menschlichen
Überprüfung.
:::

::: tip "Wie greifen Benutzer tatsächlich darauf zu?"
Über die Web-UI, Teams, Slack oder API. Die Authentifizierung wird von Ihrem bestehenden Identity Provider übernommen.
:::

::: tip "Können wir es in unsere bestehenden Tools integrieren?"
OpenAI-kompatible API für die Tool-Kompatibilität. Ereignisgesteuerte Architektur für benutzerdefinierte Integrationen.
Webhook-Endpunkte für externe Systeme.
:::

## Warum Open Source alles verändert

Das Open-Source-Lizenzmodell (siehe [LICENSES.md](https://github.com/bbvch-ai/aihub-core/blob/main/LICENSES.md) für die
Aufschlüsselung pro Paket) bedeutet, dass Sie keine Plattform adoptieren – Sie erwerben eine:

- **Kein Vendor Lock-in**: Der Code gehört Ihnen. Führen Sie ihn überall aus, passen Sie ihn nach Bedarf an
- **Keine Lizenzgebühren**: Zahlen Sie nur für die Infrastruktur, auf der Sie es betreiben
- **Transparente Operationen**: Jede Komponente ist inspizierbar und auditierbar
- **Community-gesteuert**: Verbesserungen von anderen Organisationen kommen allen zugute
- **Zukunftssicher**: Wenn wir morgen verschwinden würden, hätten Sie immer noch eine funktionierende Plattform

## Der SDK-Vorteil

Während die Plattform Infrastrukturprobleme löst, beseitigt das SDK die Entwicklungskomplexität. Das Bauen mit unserem
SDK bedeutet, dass Ihre Agents automatisch:

- Echtzeit-Updates über WebSocket-Verbindungen an Benutzer streamen
- In der Chat-Benutzeroberfläche ohne benutzerdefinierte UI-Entwicklung erscheinen
- Ohne Instrumentierungscode getraced werden
- Authentifizierung und Autorisierung ohne Sicherheitslogik handhaben
- Den Zustand in bereitgestellten Datenbanken ohne Verbindungsverwaltung speichern
- Dokumente über bestehende Pipelines ohne benutzerdefiniertes Parsing verarbeiten

Sie schreiben die Geschäftslogik. Die Plattform erledigt alles andere.

## Ein praktisches Beispiel

So sieht das Deployment Ihrer ersten KI-Funktion aus:

1. **Klonen Sie das Repository** und konfigurieren Sie Umgebungsvariablen
2. **Führen Sie `docker compose up` aus**, um die Plattform zu starten
3. **Greifen Sie auf die Web-UI zu** und authentifizieren Sie sich mit Ihrem SSO
4. **Chatten Sie mit vorgefertigten Agents**, die sofort funktionieren
5. **Verbinden Sie Ihre Datenquellen** über die Admin-Oberfläche
6. **Erstellen Sie benutzerdefinierte Agents** mit SDK-Mustern, wenn nötig

Kein Infrastruktur-Setup. Kein Service-Provisioning. Keine komplexen Konfigurationen. Die Plattform ist vom ersten Tag
an produktionsbereit.

Dies ist Infrastruktur als Produkt: vollständig, funktionsfähig und bereit für Ihre Erweiterungen.
