---
title: Unsere Lösung
source_sha: 819e0018c3a5c39b5b111a4456718df7b0a9af937f9a69092c87e3bb56c2467a
---

# Unsere Lösung: Enterprise AI-Infrastruktur als Produkt

Der Swiss AI Hub ist eine vollständige Open-Source-KI-Plattform, die Sie deployen, besitzen und kontrollieren. Es ist
kein Service, den Sie abonnieren, oder ein Framework, auf dem Sie aufbauen – es ist eine produktionsreife Infrastruktur,
die Ihnen gehört.

## Plattform + SDK: Das Komplettpaket

Der Swiss AI Hub besteht aus zwei komplementären Teilen:

**Die Plattform** ist Ihre KI-Infrastruktur. Sie ist unter der Apache 2.0 Lizenz lizenziert und enthält alles, was für
den Betrieb von KI in der Produktion benötigt wird: LLM Gateway, Vektordatenbanken, Data Pipelines, Authentifizierung,
Monitoring und Benutzeroberflächen. Deployen Sie sie mit `docker compose up` und Sie verfügen über ein funktionierendes
KI-System.

**Das SDK** ist die Art und Weise, wie Sie die Plattform erweitern. Es bietet die Muster, Tools und Frameworks für die
Entwicklung von Agents, Pipelines und Prozessen, die sich automatisch in die Plattform integrieren. Wenn Sie mit unserem
SDK entwickeln, erben Ihre Komponenten alle Plattformfunktionen – sie benötigen kein benutzerdefiniertes Deployment,
Monitoring oder Benutzerzugriff, da die Plattform dies übernimmt.

## Was Sie sofort erhalten

Wenn Sie den Swiss AI Hub deployen, verfügen Sie sofort über:

::: details Infrastruktur-Schicht
- **Vereinheitlichtes LLM Gateway** über LiteLLM, das sich mit jedem Modell-Provider verbindet
- **Vektordatenbanken** (Milvus) für semantische Suche und RAG
- **Dokumentenverarbeitung** mit MinerU für PDFs, Office-Dateien und mehr
- **Data Pipelines** mit Dagster für Ingestion und Verarbeitung
- **Message Queuing** mit NATS für ereignisgesteuerte Architektur
- **Objektspeicher** über die S3-kompatible Schicht von SeaweedFS
- **Mehrere Datenbanken** (PostgreSQL, FerretDB, ValKey) vorkonfiguriert
:::

::: details KI-Fähigkeiten
- **LLM-Zugriff über mehrere Provider** mit automatischem Failover und Kostenverfolgung
- **Integrierte RAG** mit Dokumenten-Parsing, Chunking und Retrieval
- **Agent-Orchestrierung** für komplexe mehrstufige Workflows
- **Prozessautomatisierung**, die zwischen Menschen, KI und Systemen koordiniert
- **PII-Erkennung und Anonymisierung** durch Presidio
- **Embeddings und semantische Suche** mit konfigurierbaren Modellen
:::

::: details Enterprise-Funktionen
- **SSO/OAuth-Integration** mit Ihrem Identity Provider
- **Rollenbasierte Zugriffskontrolle** mit detaillierten Berechtigungen
- **Vollständige Audit-Trails** für Compliance und Debugging
- **Kostenverfolgung und -limits** pro Benutzer, Team oder Modell
- **API-Tokens** für programmatischen Zugriff
- **Langfuse Tracing** für vollständige Observability
:::

::: details Benutzeroberflächen
- **Moderne Chat-Oberfläche** mit Sprache, Bildern und Dokumenten
- **Prozess-Cockpit** für Workflow-Monitoring und -Teilnahme
- **Admin-Dashboard** für die Systemverwaltung
- **Microsoft Teams- und Slack-Bots** für die Arbeitsumgebung der Benutzer
- **OpenAI-kompatible API** für die Integration bestehender Tools
:::

## Wie es das Infrastrukturproblem löst

Erinnern Sie sich an die schwierigen Fragen von zuvor? So beantwortet die Plattform diese:

::: tip "Wie deployen wir das?"
Alles läuft in Containern. Ein Befehl startet den gesamten Stack. Skalieren Sie durch Anpassen der Container-Anzahl.
:::

::: tip "Wo bleiben unsere Daten?"
Wo immer Sie es deployen. Betreiben Sie es On-Premise, in einem Schweizer Rechenzentrum oder in Ihrer bevorzugten Cloud.
Ihre Infrastruktur, Ihre Kontrolle.
:::

::: tip "Können wir verfolgen, was die KI tut?"
Jede Agent-Aktion wird über Langfuse getraced. Jeder API-Aufruf wird geloggt. Jede Entscheidung ist auditierbar.
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
Über die Web-UI, Teams, Slack oder API. Authentifizierung wird von Ihrem bestehenden Identity Provider übernommen.
:::

::: tip "Können wir es mit unseren bestehenden Tools integrieren?"
OpenAI-kompatible API für Tool-Kompatibilität. Ereignisgesteuerte Architektur für benutzerdefinierte Integrationen.
Webhook-Endpunkte für externe Systeme.
:::

## Warum Open Source alles verändert

Die Apache 2.0 Lizenz bedeutet, dass Sie keine Plattform adoptieren – Sie erwerben eine:

- **Kein Vendor Lock-in**: Der Code gehört Ihnen. Führen Sie ihn überall aus, ändern Sie ihn nach Bedarf.
- **Keine Lizenzgebühren**: Zahlen Sie nur für die Infrastruktur, auf der Sie es betreiben.
- **Transparente Operationen**: Jede Komponente ist inspizierbar und auditierbar.
- **Community-driven**: Verbesserungen von anderen Organisationen kommen allen zugute.
- **Zukunftssicher**: Wenn wir morgen verschwinden würden, hätten Sie immer noch eine funktionierende Plattform.

## Der SDK-Vorteil

Während die Plattform die Infrastrukturprobleme löst, vereinfacht das SDK die Entwicklungskomplexität. Das Bauen mit
unserem SDK bedeutet, dass Ihre Agents automatisch:

- Echtzeit-Updates über WebSocket-Verbindungen an Benutzer streamen
- In der Chat-Oberfläche erscheinen, ohne benutzerdefinierte UI-Entwicklung
- Ohne Instrumentierungscode getraced werden
- Authentifizierung und Autorisierung ohne Sicherheitslogik handhaben
- Den Status in bereitgestellten Datenbanken speichern, ohne Verbindungsmanagement
- Dokumente über bestehende Pipelines verarbeiten, ohne benutzerdefiniertes Parsing

Sie schreiben die Geschäftslogik. Die Plattform übernimmt alles andere.

## Ein praktisches Beispiel

So sieht das Deployment Ihrer ersten KI-Fähigkeit aus:

1. **Klonen Sie das Repository** und konfigurieren Sie Umgebungsvariablen
2. **Führen Sie `docker compose up` aus**, um die Plattform zu starten
3. **Greifen Sie auf die Web-UI zu** und authentifizieren Sie sich mit Ihrem SSO
4. **Chatten Sie mit vorgefertigten Agents**, die sofort funktionieren
5. **Verbinden Sie Ihre Datenquellen** über die Admin-Oberfläche
6. **Erstellen Sie benutzerdefinierte Agents** mit SDK-Mustern, wenn nötig

Kein Infrastruktur-Setup. Keine Service-Bereitstellung. Keine komplexen Konfigurationen. Die Plattform ist vom ersten
Tag an produktionsbereit.

Dies ist Infrastruktur als Produkt: vollständig, funktionsfähig und bereit, von Ihnen erweitert zu werden.
