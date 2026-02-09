```markdown
---
title: Unsere Lösung
source_sha: "699bd1a405f62b16767bbc75a508d154a16913cfeae07cc6101859f0f2ea0c43"
---

# Unsere Lösung: Enterprise-KI-Infrastruktur als Produkt

Der Swiss AI Hub ist eine komplette Open-Source-KI-Plattform, die Sie deployen, besitzen und kontrollieren. Es ist kein Service, den Sie abonnieren, oder ein Framework, auf dem Sie aufbauen – es ist eine produktionsreife Infrastruktur, die Ihnen gehört.

## Plattform + SDK: Das Komplettpaket

Der Swiss AI Hub besteht aus zwei komplementären Teilen:

**Die Plattform** ist Ihre KI-Infrastruktur. Apache 2.0 lizenziert, beinhaltet sie alles Notwendige, um KI in Produktion zu betreiben: LLM-Gateway, Vektordatenbanken, Daten-Pipelines, Authentifizierung, Monitoring und Benutzeroberflächen. Deployen Sie sie mit `docker compose up` und Sie haben ein funktionierendes KI-System.

**Das SDK** ist die Art und Weise, wie Sie die Plattform erweitern. Es bietet die Muster, Tools und Frameworks für den Bau von Agents, Pipelines und Prozessen, die sich automatisch in die Plattform integrieren. Wenn Sie mit unserem SDK entwickeln, erben Ihre Komponenten alle Plattformfähigkeiten – sie benötigen kein benutzerdefiniertes Deployment, Monitoring oder Benutzerzugriff, da die Plattform dies handhabt.

## Was Sie sofort erhalten

Wenn Sie den Swiss AI Hub deployen, haben Sie sofort Zugriff auf:

::: details Infrastrukturschicht
- **Vereinheitlichtes LLM-Gateway** über LiteLLM, das sich mit jedem Modell-Anbieter verbindet
- **Vektordatenbanken** (Milvus) für semantische Suche und RAG
- **Dokumentenverarbeitung** mit MinerU für PDFs, Office-Dateien und mehr
- **Daten-Pipelines** mittels Dagster für Ingestion und Verarbeitung
- **Message Queuing** mit NATS für ereignisgesteuerte Architekturen
- **Objektspeicher** über die S3-kompatible Schicht von SeaweedFS
- **Mehrere Datenbanken** (PostgreSQL, FerretDB, ValKey) vorkonfiguriert
:::

::: details KI-Funktionen
- **Multi-Provider LLM-Zugriff** mit automatischem Failover und Kostenverfolgung
- **Integriertes RAG** mit Dokumenten-Parsing, Chunking und Retrieval
- **Agent-Orchestrierung** für komplexe Multi-Step-Workflows
- **Prozessautomatisierung**, die zwischen Menschen, KI und Systemen koordiniert
- **PII-Erkennung und Anonymisierung** durch Presidio
- **Embeddings und semantische Suche** mit konfigurierbaren Modellen
:::

::: details Enterprise-Funktionen  
- **SSO/OAuth-Integration** mit Ihrem Identitätsanbieter
- **Rollenbasierte Zugriffskontrolle** mit granularen Berechtigungen
- **Vollständige Audit-Trails** für Compliance und Debugging
- **Kostenverfolgung und -limits** pro Benutzer, Team oder Modell
- **API-Tokens** für programmatischen Zugriff
- **Phoenix-Tracing** für vollständige Observability
:::

::: details Benutzeroberflächen
- **Modernes Chat-Interface** mit Sprach-, Bild- und Dokumentenunterstützung
- **Process Cockpit** für Workflow-Monitoring und -Teilnahme
- **Admin-Dashboard** für Systemverwaltung
- **Microsoft Teams und Slack Bots** für Umgebungen, in denen Benutzer bereits arbeiten
- **OpenAI-kompatible API** für die Integration bestehender Tools
:::

## Wie es das Infrastrukturproblem löst

Erinnern Sie sich an die schwierigen Fragen von zuvor? Hier ist, wie die Plattform diese beantwortet:

::: tip "Wie deployen wir das?"
Alles läuft in Containern. Ein einziger Befehl startet den gesamten Stack. Skalieren Sie durch Anpassen der Container-Anzahl.
:::

::: tip "Wo bleiben unsere Daten?"
Wo immer Sie es deployen. Betreiben Sie es On-Premise, in einem Schweizer Rechenzentrum oder in Ihrer bevorzugten Cloud. Ihre Infrastruktur, Ihre Kontrolle.
:::

::: tip "Können wir verfolgen, was die KI tut?"
Jede Agent-Aktion wird durch Phoenix getraced. Jeder API-Aufruf wird protokolliert. Jede Entscheidung ist auditierbar.
:::

::: tip "Wie kontrollieren wir die Kosten?"
LiteLLM bietet eine vereinheitlichte Kostenverfolgung über alle Modelle hinweg. Legen Sie Limits pro Benutzer, Team oder global fest.
:::

::: tip "Was passiert, wenn es fehlschlägt?"
Integrierte Fehlerbehandlung, automatisches Failover zwischen Modellen und ein sanfter Übergang zur menschlichen Überprüfung.
:::

::: tip "Wie greifen Benutzer tatsächlich darauf zu?"
Über die Web-UI, Teams, Slack oder API. Die Authentifizierung wird von Ihrem bestehenden Identitätsanbieter gehandhabt.
:::

::: tip "Können wir es in unsere bestehenden Tools integrieren?"
OpenAI-kompatible API für Tool-Kompatibilität. Ereignisgesteuerte Architektur für benutzerdefinierte Integrationen. Webhook-Endpunkte für externe Systeme.
:::

## Warum Open Source alles verändert

Die Apache 2.0 Lizenz bedeutet, dass Sie keine Plattform adoptieren – Sie erwerben eine:

- **Kein Vendor Lock-in**: Der Code gehört Ihnen. Führen Sie ihn überall aus, modifizieren Sie ihn nach Bedarf.
- **Keine Lizenzgebühren**: Zahlen Sie nur für die Infrastruktur, auf der Sie ihn betreiben.
- **Transparenter Betrieb**: Jede Komponente ist inspizierbar und auditierbar.
- **Community-getrieben**: Verbesserungen von anderen Organisationen kommen allen zugute.
- **Zukunftssicher**: Wenn wir morgen verschwinden würden, hätten Sie immer noch eine funktionierende Plattform.

## Der SDK-Vorteil

Während die Plattform die Infrastrukturprobleme löst, löst das SDK die Entwicklungskomplexität. Das Bauen mit unserem SDK bedeutet, dass Ihre Agents automatisch:

- Echtzeit-Updates über WebSocket-Verbindungen an Benutzer streamen
- Im Chat-Interface erscheinen, ohne benutzerdefinierte UI-Entwicklung
- Ohne Instrumentierungscode getraced werden
- Authentifizierung und Autorisierung ohne Sicherheitslogik handhaben
- Den Zustand in bereitgestellten Datenbanken speichern, ohne Verbindungsmanagement
- Dokumente durch bestehende Pipelines verarbeiten, ohne benutzerdefiniertes Parsing

Sie schreiben die Geschäftslogik. Die Plattform erledigt alles andere.

## Ein praktisches Beispiel

So sieht das Deployment Ihrer ersten KI-Funktion aus:

1.  **Klonen Sie das Repository** und konfigurieren Sie Umgebungsvariablen
2.  **Führen Sie `docker compose up` aus**, um die Plattform zu starten
3.  **Greifen Sie auf die Web-UI zu** und authentifizieren Sie sich mit Ihrem SSO
4.  **Chatten Sie mit vorgefertigten Agents**, die sofort funktionieren
5.  **Verbinden Sie Ihre Datenquellen** über das Admin-Interface
6.  **Erstellen Sie benutzerdefinierte Agents** unter Verwendung von SDK-Mustern, wenn nötig

Kein Infrastruktur-Setup. Keine Service-Bereitstellung. Keine komplexen Konfigurationen. Die Plattform ist vom ersten Tag an produktionsbereit.

Dies ist Infrastruktur als Produkt: vollständig, funktional und bereit, von Ihnen erweitert zu werden.
```
