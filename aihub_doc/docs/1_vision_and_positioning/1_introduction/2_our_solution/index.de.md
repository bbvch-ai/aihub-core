---
title: Unsere Lösung
index: 2
source_sha: "2aaf49d7b2f8781b9c86307f13c871ddb49e54c15a29b924aad343629897f2a1"
---

# Unsere Lösung: Enterprise AI-Infrastruktur als Produkt

Der Swiss AI Hub ist eine vollständige Open-Source AI-Plattform, die Sie deployen, besitzen und kontrollieren. Es ist kein Dienst, den Sie abonnieren, oder ein Framework, auf dem Sie aufbauen – es ist eine produktionsreife Infrastruktur, die Ihnen gehört.

## Plattform + SDK: Das Komplettpaket

Der Swiss AI Hub besteht aus zwei komplementären Teilen:

**Die Plattform** ist Ihre AI-Infrastruktur. Sie ist unter Apache 2.0 lizenziert und enthält alles, was für den Betrieb von AI in der Produktion erforderlich ist: LLM-Gateway, Vektordatenbanken, Datenpipelines, Authentifizierung, Monitoring und Benutzeroberflächen. Deployen Sie sie mit `docker compose up` und Sie haben ein funktionierendes AI-System.

**Das SDK** ist die Art und Weise, wie Sie die Plattform erweitern. Es bietet die Muster, Tools und Frameworks für die Entwicklung von Agenten, Pipelines und Prozessen, die sich automatisch in die Plattform integrieren. Wenn Sie mit unserem SDK entwickeln, erben Ihre Komponenten alle Plattformfunktionen – sie benötigen keine individuelle Bereitstellung, Überwachung oder Benutzerzugriff, da die Plattform dies alles übernimmt.

## Was Sie sofort erhalten

Wenn Sie den Swiss AI Hub deployen, verfügen Sie sofort über:

::: details Infrastrukturebene
-   **Einheitliches LLM-Gateway** über LiteLLM, das sich mit jedem Modell-Anbieter verbindet
-   **Vektordatenbanken** (Milvus) für semantische Suche und RAG
-   **Dokumentenverarbeitung** mit Docling für PDFs, Office-Dateien und mehr
-   **Datenpipelines** mit Dagster für Ingestion und Verarbeitung
-   **Nachrichtenwarteschlangen** mit NATS für ereignisgesteuerte Architekturen
-   **Objektspeicher** über eine MinIO S3-kompatible Schicht
-   **Mehrere Datenbanken** (PostgreSQL, MongoDB, Redis) vorkonfiguriert
:::

::: details KI-Funktionen
-   **LLM-Zugriff über mehrere Anbieter** mit automatischem Failover und Kostenverfolgung
-   **Eingebautes RAG** mit Dokumenten-Parsing, Chunking und Retrieval
-   **Agenten-Orchestrierung** für komplexe mehrstufige Workflows
-   **Prozessautomatisierung**, die Menschen, KI und Systeme koordiniert
-   **PII-Erkennung und -Anonymisierung** durch Presidio
-   **Embeddings und semantische Suche** mit konfigurierbaren Modellen
:::

::: details Enterprise-Funktionen
-   **SSO/OAuth-Integration** mit Ihrem Identitätsanbieter
-   **Rollenbasierte Zugriffskontrolle** mit granularen Berechtigungen
-   **Vollständige Audit-Trails** für Compliance und Debugging
-   **Kostenverfolgung und -limits** pro Benutzer, Team oder Modell
-   **API-Tokens** für programmatischen Zugriff
-   **Phoenix-Tracing** für vollständige Observabilität
:::

::: details Benutzeroberflächen
-   **Moderne Chat-Oberfläche** mit Sprache, Bildern und Dokumenten
-   **Prozess-Cockpit** für Workflow-Überwachung und -Teilnahme
-   **Admin-Dashboard** für die Systemverwaltung
-   **Microsoft Teams- und Slack-Bots** für die Arbeitsumgebung der Benutzer
-   **OpenAI-kompatible API** für die Integration bestehender Tools
:::

## Wie es das Infrastrukturproblem löst

Erinnern Sie sich an die schwierigen Fragen von zuvor? Hier erfahren Sie, wie die Plattform sie beantwortet:

::: tip „Wie deployen wir das?"
Alles läuft in Containern. Ein Befehl startet den gesamten Stack. Skalieren Sie durch Anpassen der Container-Anzahl.
:::

::: tip „Wo bleiben unsere Daten?"
Wo immer Sie es deployen. Betreiben Sie es on-premise, in einem Schweizer Rechenzentrum oder in Ihrer bevorzugten Cloud. Ihre Infrastruktur, Ihre Kontrolle.
:::

::: tip „Können wir verfolgen, was die KI tut?"
Jede Agentenaktion wird über Phoenix nachverfolgt. Jeder API-Aufruf wird protokolliert. Jede Entscheidung ist auditierbar.
:::

::: tip „Wie kontrollieren wir die Kosten?"
LiteLLM bietet eine vereinheitlichte Kostenverfolgung für alle Modelle. Legen Sie Limits pro Benutzer, Team oder global fest.
:::

::: tip „Was passiert, wenn es fehlschlägt?"
Eingebautes Fehlerhandling, automatisches Failover zwischen Modellen und anmutige Degradation zur menschlichen Überprüfung.
:::

::: tip „Wie greifen Benutzer tatsächlich darauf zu?"
Über die Web-UI, Teams, Slack oder API. Die Authentifizierung wird von Ihrem bestehenden Identitätsanbieter übernommen.
:::

::: tip „Können wir es in unsere bestehenden Tools integrieren?"
OpenAI-kompatible API für die Tool-Kompatibilität. Ereignisgesteuerte Architektur für individuelle Integrationen. Webhook-Endpunkte für externe Systeme.
:::

## Warum Open Source alles verändert

Die Apache 2.0-Lizenz bedeutet, dass Sie keine Plattform einführen – Sie erwerben eine:

-   **Kein Vendor Lock-in**: Der Code gehört Ihnen. Führen Sie ihn überall aus, passen Sie ihn nach Bedarf an
-   **Keine Lizenzgebühren**: Zahlen Sie nur für die Infrastruktur, auf der Sie es betreiben
-   **Transparenter Betrieb**: Jede Komponente ist überprüfbar und auditierbar
-   **Community-gesteuert**: Verbesserungen von anderen Organisationen kommen allen zugute
-   **Zukunftssicher**: Wenn wir morgen verschwinden würden, hätten Sie immer noch eine funktionierende Plattform

## Der SDK-Vorteil

Während die Plattform die Infrastruktur löst, behebt das SDK die Komplexität der Entwicklung. Das Bauen mit unserem SDK bedeutet, dass Ihre Agenten automatisch:

-   Echtzeit-Updates über WebSocket-Verbindungen an Benutzer streamen
-   in der Chat-Oberfläche erscheinen, ohne dass eine individuelle UI-Entwicklung erforderlich ist
-   ohne Instrumentierungscode nachverfolgt werden
-   Authentifizierung und Autorisierung ohne Sicherheitslogik verwalten
-   den Zustand in bereitgestellten Datenbanken speichern, ohne Verbindungsmanagement
-   Dokumente über bestehende Pipelines verarbeiten, ohne individuelles Parsing

Sie schreiben die Geschäftslogik. Die Plattform übernimmt den Rest.

## Ein praktisches Beispiel

So sieht das Deployment Ihrer ersten KI-Funktionalität aus:

1.  **Klonen Sie das Repository** und konfigurieren Sie Umgebungsvariablen
2.  **Führen Sie `docker compose up` aus**, um die Plattform zu starten
3.  **Greifen Sie auf die Web-UI zu** und authentifizieren Sie sich mit Ihrem SSO
4.  **Chatten Sie mit vorgefertigten Agenten**, die sofort funktionieren
5.  **Verbinden Sie Ihre Datenquellen** über die Admin-Oberfläche
6.  **Erstellen Sie bei Bedarf individuelle Agenten** mit SDK-Mustern

Keine Infrastruktur-Einrichtung. Keine Service-Bereitstellung. Keine komplexen Konfigurationen. Die Plattform ist vom ersten Tag an produktionsbereit.

Das ist Infrastruktur als Produkt: vollständig, funktional und bereit für Ihre Weiterentwicklung.
