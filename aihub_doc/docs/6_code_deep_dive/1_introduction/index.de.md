---
title: Einführung
index: 1
source_sha: "b98ca113b2f42a2f0b7b7fa70927f1d626d02ede99d592f11a93bc423bed1d5a"
---

# AI-Hub Entwicklerhandbuch

## 1. :rocket: Einführung

### Was ist der Swiss AI-Hub?

::: info
Der Swiss AI-Hub ist eine umfassende, unternehmensgerechte Plattform, die entwickelt wurde, um Künstliche Intelligenz in den
Kern Ihres Unternehmens zu integrieren. Sie begegnet einem kritischen Bedarf auf dem Schweizer Markt
nach einer souveränen, vertrauenswürdigen und kollaborativen KI-Plattform.
:::

Die meisten verfügbaren KI-Tools sind Frameworks oder Bibliotheken, die sich hervorragend für
Machbarkeitsstudien eignen, den Benutzer jedoch vor die immense Herausforderung stellen,
ein sicheres, skalierbares und wartbares, unternehmenstaugliches System aufzubauen.
Der Swiss AI-Hub schliesst diese Lücke, indem er ein komplettes, produktionsreifes Ökosystem
für Schweizer Unternehmen bereitstellt, um mit KI erfolgreich zu sein, und nicht nur ein weiteres Agenten-Framework.
Es ist ein grundlegendes Software-Framework, das als Brücke zwischen Menschen, Unternehmenswissen
und digitalen Prozessen dient. Ein Kernprinzip des Hubs ist es, spezialisierte Intelligenz
direkt in vertraute Arbeitsumgebungen zu bringen, anstatt Mitarbeiter dazu zu zwingen,
zwischen speziellen Anwendungen für KI-Unterstützung zu wechseln.

### Unser Ziel: Eine unternehmensgerechte Plattform, nicht nur eine Bibliothek

Die Unterscheidung zwischen einer Bibliothek und einer Plattform ist zentral für unsere Vision.
Während eine Bibliothek Ihnen hilft, ein spezifisches Problem zu lösen, bietet eine Plattform
die gesamte Umgebung, um Probleme im grossen Massstab, zuverlässig und langfristig zu lösen.

::: tip :battery: Batterien inbegriffen!
Der Swiss AI-Hub ist eine "Batterien inbegriffen"-Plattform für Entwickler. Sie bietet
eine vollwertige Unternehmensarchitektur, einschliesslich:

- Einer Datenbankschicht
- Einer REST-API und eines WebSocket-Gateways
- Einer Benutzeroberfläche
- Skalierbarer Datenaufnahmepipelines
- Vorkonfigurierter Docker-Container für die Bereitstellung
:::

Dies ermöglicht es Entwicklern, sich auf die Schaffung von Geschäftswert zu konzentrieren, indem sie die Logik eines Agenten entwerfen, während die Plattform Sicherheit, Skalierbarkeit und Infrastruktur übernimmt.

### Kernphilosophie: Der "Schweizer Weg"

Unsere Architektur basiert auf einer Reihe nicht verhandelbarer Prinzipien, die die Werte
der Unternehmen widerspiegeln, denen wir dienen.

::: warning :shield: Nicht verhandelbare Prinzipien
- **Datenschutz und Souveränität durch Design**: Die Plattform ist so konzipiert, dass
  sie vollständig selbst hostbar ist, wodurch der gesamte Technologiestack On-Premise
  oder in einer Schweizer Cloud betrieben werden kann. Dies garantiert vollständige
  Datensouveränität und stellt sicher, dass sensible Unternehmensdaten in der Schweiz
  verbleiben und Schweizer Vorschriften unterliegen.
- **Sicherheit als Voraussetzung**: Sicherheit ist in jeder Schicht der Architektur integriert,
  von einem sicheren Entwicklungslebenszyklus bis hin zu granularer Zugriffskontrolle und Unterstützung
  für Unternehmensauthentifizierung wie OAuth und LDAP. Es ist ein Prinzip, das jede architektonische
  Entscheidung prägt, und nicht ein nachträgliches Add-on ist.
- **Radikale Transparenz und Auditierbarkeit**: Wir glauben, dass Vertrauen durch Transparenz gewonnen wird.
  Unsere "KI-Agenten als Workflows"-Philosophie stellt sicher, dass das Verhalten von Agenten
  keine "Black Box" ist. Agenten und Assistenten werden als strukturierte, schrittweise Workflows
  erstellt, wodurch sie inhärent transparent und testbar sind. Jeder Schritt kann visuell überwacht
  und auditiert werden, unter Verwendung von Tools wie Phoenix Tracing, was entscheidend ist,
  um das Vertrauen von Mitarbeitern, Managern und Aufsichtsbehörden zu gewinnen.
:::

### Die Vision: Von Assistenten zu autonomen Agenten

Der AI-Hub ist darauf ausgelegt, mit einer Organisation zu wachsen und eine evolutionäre Reise
von einfacher Unterstützung zu autonomer Prozessautomatisierung zu begleiten. Er ermöglicht die
Schaffung eines reichen Ökosystems spezialisierter KI-Lösungen, die mit Ihrem Team zusammenarbeiten.

::: details :robot: KI-Assistenten: Ihr KI-gestützter Co-Worker
Für Mitarbeiter bietet der AI-Hub sicheren Zugang zu spezialisierten KI-Assistenten,
die auf die Bedürfnisse Ihres Teams zugeschnitten sind. Im Gegensatz zu generischen Chatbots
sind diese Assistenten wertvoll, weil sie mit relevanten Geschäftsdaten und -tools integriert sind.
Sie sind reaktive, kontextbewusste Partner, die darauf ausgelegt sind, Ihre tägliche Arbeit zu verbessern,
indem sie komplexe Fragen beantworten, Daten analysieren und Ihnen Zeit und Mühe ersparen.
:::

::: details :gear: KI-Agenten: Autonome Prozesspartner
Wenn eine Organisation Fortschritte macht, ermöglicht die Plattform die Zusammenarbeit
mit KI-Agenten – autonomen Partnern, die proaktiv an Geschäftsprozessen teilnehmen.
Anstatt nur auf Prompts zu reagieren, sind diese Agenten darauf ausgelegt, Workflows
zu analysieren, autonom die nächsten Schritte zu bestimmen und Aufgaben mit minimalem
menschlichem Eingriff auszuführen. Dies gestaltet Workflows als eine tiefe Zusammenarbeit
zwischen Menschen und KI neu, sodass Mitarbeiter sich auf die kritischsten und kreativsten
Aspekte ihrer Arbeit konzentrieren können, während sie die Aufsicht über wichtige Entscheidungen behalten.
:::

---

## 2. :file_folder: Projektstruktur & Repositories

Der Swiss AI-Hub ist als leistungsstarkes, kohärentes Ökosystem konzipiert. Seine Struktur ist nicht nur eine technische Entscheidung; sie ist ein Ausdruck unserer Vision, eine Plattform bereitzustellen, die sowohl sofort einsatzbereit als auch unendlich erweiterbar ist.

### Repository-Typen: Core vs. Kunde

Das Ökosystem ist in zwei grundlegende Typen von Repositories organisiert, um eine saubere Trennung der Verantwortlichkeiten zu gewährleisten und die Zusammenarbeit zu fördern, ohne Datenlecks zu riskieren.

::: danger :warning: Kritische Trennung
- **Core Repository (`aihub-core`)**: Dies ist das Herz der Plattform. Es enthält die gesamte gemeinsam genutzte, wiederverwendbare Funktionalität und den Code, der den AI-Hub antreibt. Unter keinen Umständen sollte es kundenspezifische Informationen enthalten. Diese strikte Trennung ist entscheidend, da `aihub-core` von allen kundenspezifischen Projekten als Abhängigkeit referenziert wird.
- **Kunden-Repositories (`aihub-<KUNDE>`)**: Diese Repositories sind der Ort, an dem Sie den Hub für einen spezifischen Kontext zum Leben erwecken. Sie bauen auf dem leistungsstarken Fundament von `aihub-core` auf und ermöglichen es Ihnen, Komponenten – wie Agenten, Pipelines oder Prozesse – für die Bedürfnisse eines spezifischen Kunden hinzuzufügen oder zu überschreiben.
:::

### Eine Architektur für Geschwindigkeit und Erweiterbarkeit

Für einen Entwickler ist der AI-Hub eine komplette "Batterien inbegriffen"-Plattform, nicht nur eine Bibliothek. Das Monorepo enthält mehrere, eigenständige Python-Pakete, genannt "Scopes", die in logische Schichten organisiert sind. Diese Architektur wurde entwickelt, um Ihnen zu ermöglichen, sich auf die Schaffung von Geschäftswert zu konzentrieren, während wir die Schwerstarbeit in Bezug auf Infrastruktur, Sicherheit und Skalierbarkeit übernehmen.

::: details :building_construction: Die Fundament- & Logikschichten
Auf der untersten Ebene befindet sich **`aihub_lib`**, die grundlegende gemeinsame Bibliothek für Code, der von mehr als einem Dienst verwendet wird. Darauf aufbauend bieten wir eine Basisschicht für die Kern-KI-Komponenten:

- **`aihub_pipeline`**: Enthält Definitionen für Datenaufnahme- und Verarbeitungspipelines, oft unter Verwendung von Dagster.
- **`aihub_agents`**: Enthält die gesamte agentenspezifische Logik und Workflow-Definitionen.
- **`aihub_process`**: Orchestriert hochrangige Geschäftsprozesse, die die Zusammenarbeit zwischen Agenten, Menschen und externen Programmen umfassen.
:::

::: details :electric_plug: Die Integrations- & Interaktionsschicht
Diese Schicht bietet eine Full-Stack-Erfahrung für die Interaktion mit der Kernlogik.

- **`aihub_api`**: Die wichtigste benutzerorientierte REST-API und das WebSocket-Gateway, erstellt mit FastAPI.
- **`aihub_web`**: Die vollständige Frontend-Anwendung, erstellt mit Nuxt.js, die die Benutzeroberfläche bereitstellt.
- **`aihub_bot`**: Die Kernlogik für die Integration mit Kollaborationsplattformen wie MS Teams.
:::

::: details :toolbox: Die Betriebs- & Best Practices-Schicht
Wir bieten Tools, um sicherzustellen, dass Ihre Lösungen robust, wartbar und einfach bereitzustellen sind.

- **`aihub_action`**: Enthält wiederverwendbare GitHub Actions zur Standardisierung von CI/CD-Pipelines und zur Vermeidung von Duplikaten.
- **`aihub_iac`**: (Infrastructure-as-Code) Definiert wiederverwendbare Cloud-Infrastrukturressourcen für die Bereitstellung.
- **`aihub_doc`**: Enthält die gesamte Projektdokumentation, einschliesslich arc42 und Architectural Decision Records (ADRs).
:::

### Sofort einsatzbereit oder anpassbar

::: tip :package: Sofortiger Start
Diese Architektur bietet Ihnen unglaubliche Flexibilität. Sie können den Hub unverändert nutzen, indem Sie einfach die `docker-compose.yaml` ausführen, um einen voll funktionsfähigen, lokal laufenden AI-Hub mit vorgefertigten Standardagenten, Pipelines und Prozessen zu erhalten, die sofort einsatzbereit sind.
:::

::: info :sparkles: Die Magie der Erweiterung
Oder Sie können ihn erweitern. Hier geschieht die Magie. Wenn Sie Ihre eigenen Komponenten erstellen, bauen Sie auf derselben praxiserprobten Basis auf, die wir auch verwenden. Erstellen Sie einen neuen Agenten, eine neue Pipeline oder einen neuen Prozess, verpacken Sie es als Docker-Image und fügen Sie es der `docker-compose.yaml` hinzu. Sofort wird Ihre Kreation zu einem erstklassigen Element im Ökosystem. Sie werden sehen, dass alle unsere Plattformfunktionen automatisch und sofort für Ihre Komponente funktionieren:

- **Automatische Observability**: Ihr neuer Agent wird sofort in der **`aihub_web`** Benutzeroberfläche erscheinen, wo er verwaltet und beobachtet werden kann.
- **Integrierte Nachvollziehbarkeit**: Jeder Lauf Ihres Agenten wird automatisch nachverfolgt und kann visuell in Phoenix auditiert werden, ohne zusätzlichen Aufwand.
- **Nahtlose Interaktion**: Ihr Agent kann über die Chat-Oberfläche aufgerufen werden und unsere integrierten Protokolle verwenden, um mit anderen Agenten im Hub zu interagieren.
- **Prozessintegration**: Sie können Ihren neuen Agenten sofort als Schritt innerhalb eines grösseren, komplexeren Agentenprozesses mittels **`aihub_process`** einsetzen.

Möchten Sie eine neue Pipeline in **`aihub_pipeline`** erstellen, die Daten in einen bestehenden, perfektionierten RAG-Agenten, den wir bereits bereitstellen, aufnimmt und einspeist? Das können Sie. Der Hub ist für diese Art der leistungsstarken, modularen Komposition konzipiert. Sie konzentrieren sich auf die einzigartige Logik, und die Plattform erledigt den Rest.
:::

---

## 3.:computer: Erste Schritte: Lokale Entwicklungsumgebung einrichten

Dieses Kapitel beschreibt die im AI-Hub verwendeten Technologien und die notwendigen Schritte zur Einrichtung der Entwicklungsumgebung über die Kommandozeile. Es obliegt dem Entwickler, die benötigten Tools entsprechend seinem Betriebssystem und seinen Präferenzen zu installieren.

### Erforderliche Technologien

::: details :wrench: Vollständiger Technologie-Stack
Das AI-Hub-Projekt nutzt die folgenden Technologien. Stellen Sie sicher, dass diese installiert und von Ihrer Kommandozeilenumgebung aus zugänglich sind.

- **Git**: Für die Versionskontrolle.
- **Python**: Das Projekt basiert auf Python, spezifisch Version 3.13.
- **Poetry**: Für das Abhängigkeitsmanagement und die Verwaltung virtueller Umgebungen für jedes Python-Paket.
- **make**: Wird zum Ausführen gängiger Aufgaben und Befehle verwendet, die in Makefiles definiert sind.
- **Docker & Docker Compose**: Für die Containerisierung und den Betrieb des Infrastruktur-Stacks des Projekts.
- **Node.js**: Die LTS-Version wird für die Frontend-Entwicklung verwendet, verwaltet über einen Versionsmanager wie NVM.
- **pnpm**: Schneller Paketmanager für Node.js.
- **Weitere Tools**: Für spezifische Aufgaben benötigen Entwickler möglicherweise auch Tools wie **Postman** für API-Tests, **MongoDB Compass** für die Datenbankverwaltung und den **Bot Framework Emulator** zum Testen von Chatbots.
:::

#### :robot: KI & LLM Orchestrierung

Unsere KI-Fähigkeiten werden hauptsächlich durch das LlamaIndex-Ökosystem und Integrationen mit führenden KI-Anbietern unterstützt.

- **LlamaIndex**: Das zentrale Framework zum Erstellen kontextbewusster RAG (Retrieval-Augmented Generation)-Anwendungen. Dies umfasst `llama-index-core` sowie verschiedene Integrationen für Vektorspeicher, Embeddings und LLMs.
- **LLM- & Embedding-Anbieter**:
  - **OpenAI & Azure OpenAI**: Integriert über die Bibliotheken `openai`, `llama-index-llms-openai-like` und
    `llama-index-embeddings-azure-openai`.
  - **Google GenAI**: Unterstützung für Googles Modelle über `google-genai` und `llama-index-llms-google-genai`.
  - **Hugging Face**: Verwendung von `transformers` und `llama-index-embeddings-text-embeddings-inference` für lokale oder
    selbst gehostete Modelle.
- **Azure AI Services**: Wir nutzen Azure's verwaltete KI-Dienste umfassend, einschliesslich:
  - **Azure Cognitive Search**: Für leistungsstarke Such- und Abruffunktionen.
  - **Azure Document Intelligence**: Für Dokumentenanalyse und Informationsgewinnung.
  - **Azure Speech Services**: Für Spracherkennung und andere sprachbezogene Funktionen.

#### :floppy_disk: Daten & Speicherung

- **Datenbanken**:
  - **MongoDB**: Wird als unsere primäre NoSQL-Datenbank verwendet, zugänglich über **MongoEngine** und in LlamaIndex zur Dokumentspeicherung (`llama-index-storage-docstore-mongodb`) integriert.
  - **Redis**: Für In-Memory-Caching und schnellen Datenabruf.
- **Vektorspeicher**:
  - **Azure AI Search**: Der primäre Vektorspeicher für unsere Produktionsumgebung (
    `llama-index-vector-stores-azureaisearch`).
  - **Milvus**: Eine alternative oder zusätzliche Vektordatenbankoption (`llama-index-vector-stores-milvus`).
- **Dateispeicher**:
  - **Azure Data Lake Storage (ADLS)**: Verwaltet über `azure-storage-file-datalake` und `adlfs` für die grossflächige Datenspeicherung und den Zugriff.

#### :satellite: Observability & Kommunikation

- **Monitoring**: Wir verwenden eine Kombination von Tools für eine umfassende Anwendungsüberwachung:
  - **OpenTelemetry**: Das grundlegende Toolkit zum Generieren und Exportieren von Telemetriedaten (Traces, Metriken, Logs).
  - **OpenInference**: Eine spezialisierte Instrumentierungsbibliothek für das Monitoring von LLM-Anwendungen, die mit LlamaIndex erstellt wurden.
  - **Arize Phoenix**: Für ML Observability und Modellleistungsbewertung.
- **Asynchrone Nachrichtenübermittlung**:
  - **NATS**: Wird für leistungsstarke, asynchrone Kommunikation zwischen Diensten verwendet.

#### :sparkles: Codequalität & Tooling

Wir setzen strenge Standards durch, um sicherzustellen, dass unser Code sauber, konsistent und fehlerfrei ist.

- **Linting & Formatierung**:
  - **Ruff**: Unser primärer Linter für Geschwindigkeit und umfassende Prüfungen.
  - **Black**: Für kompromisslose und konsistente Code-Formatierung.
- **Typ-Prüfung**:
  - **MyPy**: Wird im `strict`-Modus verwendet, um statische Typensicherheit über die gesamte Codebasis zu erzwingen.
- **Testen**:
  - **Pytest**: Das Kern-Framework zum Schreiben und Ausführen unserer Tests, zusammen mit `pytest-asyncio` für asynchronen Code und `pytest-mock` für Mocking.
  - **Pytest BDD**: Für das Schreiben verhaltensgesteuerter Tests.

### :gear: Codebasis & Abhängigkeits-Setup

#### Repositories klonen

::: info
Klonen Sie zuerst die erforderlichen Repositories in Ihren lokalen Arbeitsbereich.

- **aihub-core** (dieses Repo): `git clone https://github.com/bbvch-ai/aihub-core`
:::

#### Projektabhängigkeiten installieren

Das Projekt ist ein Monorepo, das mehrere Pakete ("Scopes") enthält, wie `aihub_agent` oder `aihub_api`. Jeder Scope hat seine eigene isolierte Poetry-Umgebung und Abhängigkeiten.

::: warning :warning: Wichtig
Um an einem spezifischen Scope zu arbeiten, müssen Sie zuerst dessen Umgebung aktivieren:

1. Navigieren Sie in das Verzeichnis des Scopes (z.B. `cd aihub_agent`).
2. Aktivieren Sie die Umgebung mit dem Befehl: `poetry shell`. Poetry shell wurde in ein separates Plugin verschoben, daher müssen Sie es möglicherweise zuerst mit `poetry self add poetry-plugin-shell` installieren.
3. Sobald die Shell aktiviert ist, installieren Sie die Abhängigkeiten mit: `poetry install`.

Sie müssen Befehle innerhalb der aktivierten Umgebung des korrekten Scopes ausführen. Dieser Prozess muss für jeden Scope wiederholt werden, an dem Sie arbeiten möchten.
:::

Für Frontend-Dienste (`aihub_web`) folgen Sie den Einrichtungsanweisungen in der `README.md`-Datei dieses Verzeichnisses.

#### Abhängigkeiten mit Poetry verwalten

::: tip :package: Poetry-Befehle
Verwenden Sie die folgenden Befehle, um Abhängigkeiten innerhalb einer aktivierten Scope-Umgebung zu verwalten. Bearbeiten Sie die Dateien `pyproject.toml` oder `poetry.lock` nicht manuell.

- `poetry install`: Installiert alle in `poetry.lock` definierten Abhängigkeiten.
- `poetry add <package>`: Fügt ein neues Paket als Abhängigkeit hinzu.
- `poetry remove <package>`: Entfernt ein Paket.
- `poetry update`: Aktualisiert alle Abhängigkeiten auf ihre neuesten zulässigen Versionen.
:::

### :whale: Starten des Infrastruktur-Stacks (Docker)

Um den vollständigen AI-Hub-Stack lokal auszuführen, verwenden Sie Docker Compose, um die erforderlichen Dienste zu starten. Für verschiedene Umgebungen stehen mehrere Konfigurationsdateien zur Verfügung. Führen Sie den entsprechenden Befehl aus dem Stammverzeichnis des `aihub-core`-Repositories aus:

::: tip :whale: Wählen Sie Ihre Umgebung
**Für eine CPU-Umgebung**:

```bash
docker compose -f docker-compose.yml -f milvus-standalone-docker-compose.yml -f docker-compose-webui.yml up -d
```

**Für eine GPU-Umgebung**:

```bash
docker compose -f milvus-standalone-docker-compose.yml -f docker-compose-webui.yml -f docker-compose-gpu.yml up -d
```
:::

::: warning :clock3: Warten Sie auf den Health Check
Warten Sie, bis alle Dienste fehlerfrei sind (Sie können dies mit `docker ps` überprüfen), bevor Sie fortfahren.
:::

### :house: Den AI-Hub lokal ausführen

::: warning :warning: Wichtig
Verwenden Sie selbstsignierte SSL-Zertifikate nur für die lokale Entwicklung. Verwenden Sie diese niemals in Produktions- oder öffentlichen Umgebungen.
:::

Für die lokale Entwicklung mit SSL-Unterstützung und benutzerdefiniertem Domain-Routing verwenden Sie die Konfiguration `docker-compose.local.yml`:

#### Voraussetzungen

1. **mkcert**: Installieren Sie mkcert zur Generierung lokaler SSL-Zertifikate

   - **Linux (Ubuntu/Debian)**:
     ```bash
     sudo apt install libnss3-tools
     wget -O mkcert https://dl.filippo.io/mkcert/latest?for=linux/amd64
     chmod +x mkcert
     sudo mv mkcert /usr/local/bin/
     ```
   - **Windows**:
     ```powershell
     # Using Chocolatey
     choco install mkcert

     # Using Scoop
     scoop bucket add extras
     scoop install mkcert
     ```

2. **SSL-Zertifikate generieren**:

   ```bash
   make local-cert
   ```

3. **Umgebungskonfiguration**:

   - Kopieren Sie `.env.dev` nach `.env` und konfigurieren Sie es mit Ihren Einstellungen
   - Die Standarddomäne `127.0.0.1.nip.io` bietet eine Wildcard-DNS-Auflösung auf localhost

#### Lokalen Stack starten

```bash
# Start all services with local configuration
docker compose -f docker-compose.local.yml up -d

# Check service health
docker compose -f docker-compose.local.yml ps
```

#### Zugriffspunkte

Sobald gestartet, greifen Sie auf die AI-Hub-Dienste unter zu:

- **Haupt-Weboberfläche**: https://127.0.0.1.nip.io
- **OpenWebUI**: https://openwebui.127.0.0.1.nip.io
- **LiteLLM**: https://litellm.127.0.0.1.nip.io
- **Dagster**: https://dagster.127.0.0.1.nip.io
- **MinIO Konsole**: https://datalake.127.0.0.1.nip.io
- **Traefik Dashboard**: https://traefik.localhost (Administrator-Zugangsdaten erforderlich)

::: tip :bulb: Tipps zur lokalen Entwicklung
- Die `.nip.io`-Domain löst automatisch zu Ihrem Localhost auf und bietet so ein produktionsähnliches Domain-Erlebnis
- SSL-Zertifikate sind sowohl für `*.127.0.0.1.nip.io`- als auch für `*.localhost`-Domains gültig
- Alle Dienste verwenden Traefik für SSL-Terminierung und Routing
- Volumendaten werden in `${VOLUME_ROOT:-./.docker-volumes}/` gespeichert (Standard ist `.docker-volumes/`)
:::

### :key: Umgebungsvariablen konfigurieren

::: warning
Das Projekt benötigt Umgebungsvariablen für die Konfiguration. Sie müssen die `.env`-Dateien vom Team anfordern und diese in den Stammverzeichnissen der relevanten Backend- und Frontend-Projekte platzieren.
:::

### :robot: KI-Programmierassistenten-Integration (MCP)

Der AI-Hub bietet eine verbesserte Integration mit KI-Programmierassistenten über das Model Context Protocol (MCP). Diese Integration ermöglicht es KI-Tools wie Claude Code, Gemini CLI und anderen Assistenten, direkt mit Ihrer Entwicklungsumgebung zu interagieren.

::: info MCP-Vorteile
Die MCP-Integration bietet KI-Programmierassistenten Folgendes:

- **Echtzeit-Beobachtung** laufender Dienste und deren Zustand
- **Direkter Zugriff** auf Entwicklungsdatenbanken zum Debuggen
- **API-Interaktionsfähigkeiten** für Tests und Validierung
- **Observability-Integration** mit Phoenix-Tracing und -Monitoring
:::

#### :gear: MCP-Konfiguration

Die MCP-Integration wird über die Datei `.mcp.json` im Projekt-Root konfiguriert. Diese Datei definiert drei wichtige MCP-Server:

1. **Phoenix MCP Server**: Bietet Zugriff auf KI-Observability- und Tracing-Daten
2. **MongoDB MCP Server**: Ermöglicht Datenbankabfragen und -überwachung (schreibgeschützt)
3. **AI-Hub API MCP Server**: Exponiert AI-Hub API-Funktionalität gegenüber KI-Assistenten

::: details :wrench: MCP-Server-Konfiguration
Die Datei `.mcp.json` enthält die folgende Konfiguration:

```json
{
  "mcpServers": {
    "phoenix": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "--network=host",
        "node:22-alpine",
        "npx",
        "-y",
        "@arizeai/phoenix-mcp@latest",
        "--baseUrl",
        "http://localhost:6006"
      ]
    },
    "mongodb": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "--network=host",
        "-e",
        "MDB_MCP_CONNECTION_STRING=mongodb://admin:admin@localhost:27017/aihub",
        "-e",
        "MDB_MCP_READ_ONLY=true",
        "mongodb/mongodb-mcp-server:latest"
      ]
    },
    "aihub_api": {
      "type": "http",
      "url": "http://localhost:8000/mcp",
      "disabled": false,
      "autoApprove": []
    }
  }
}
```
:::

#### :rocket: MCP-Integration nutzen

Sobald Ihre Entwicklungsumgebung läuft, können KI-Programmierassistenten, die MCP unterstützen, diese Integrationen automatisch erkennen und nutzen:

- **Abfrage von Agenten-Ausführungstraces** über Phoenix MCP
- **Inspektion des Datenbankzustands** über MongoDB MCP (schreibgeschützt)
- **Testen von API-Endpunkten** über AI-Hub API MCP
- **Debuggen komplexer Probleme** mit vollem Entwicklungskontext

::: tip KI-Assistenten-Setup
Stellen Sie sicher, dass Ihr KI-Programmierassistent (Claude Code, Gemini CLI usw.) so konfiguriert ist, dass er die Datei `.mcp.json` verwendet. Die meisten modernen KI-Assistenten erkennen und verwenden diese Konfiguration automatisch, wenn sie im Projekt-Root vorhanden ist.
:::

### :hammer_and_wrench: Entwicklungstools & Slash-Befehle

Der AI-Hub enthält mehrere Slash-Befehle (im Verzeichnis `.claude/commands/`), die gängige Entwicklungsworkflows rationalisieren:

- **`/create-pr`**: Pre-Pull-Request-Validierung und -Vorbereitung
- **`/update-doc`**: Dokumentationssynchronisierung und -aktualisierungen
- **`/document-decisions`**: ADR-Erstellung und -Verwaltung
- **`/document-feature`**: Erstellen von Dokumentation für eine beschriebene Funktion
- **`/explain`**: Erklärt und dokumentiert einen spezifischen Teil der Codebasis
- **`/implement-feedback-from-pr`**: Systematische PR-Feedback-Implementierung

::: info KI-Assistenten-Kontextdateien
Jeder Scope enthält `CLAUDE.md`- und `GEMINI.md`-Dateien, die auf die jeweiligen README-Dateien verweisen. Diese stellen KI-Assistenten den richtigen Kontext über den Zweck und die Architektur jeder Komponente bereit.
:::

---

## 4. :clipboard: Projekt-Governance & Arbeitsmanagement

Dieses Kapitel beschreibt die Regeln und Prozesse, die Beiträge, technische Entscheidungsfindung und die Verwaltung der Entwicklungsarbeit im gesamten Projekt regeln.

### :chart_with_upwards_trend: Arbeitsmanagement (Roadmap & Kanban)

Das AI-Hub-Ökosystem nutzt zwei Haupt-GitHub-Projekte, um die Entwicklung und die übergeordnete Planung zu verwalten. Alle Interaktionen können über das GitHub CLI (`gh`) durchgeführt werden.

#### Hochrangige Planung: `aihub-roadmap`

Das `aihub-roadmap`-Projekt konzentriert sich auf die hochrangige Planung, einschliesslich Kundenprojekte und grösserer Initiativen für den AI-Hub-Kern. Hier finden Sie allgemeine Projektinformationen, Ziele und laufende Dokumentation zu wichtigen Initiativen.

::: details :chart_with_upwards_trend: Roadmap-Zugriff
**URL**: `https://github.com/orgs/bbvch-ai/projects/7`

**Roadmap via CLI anzeigen**:

```bash
# View high-level details of the roadmap project
gh project view 7 --owner bbvch-ai

# List all items in the roadmap
gh project item-list 7 --owner bbvch-ai
```
:::

#### Tägliche Arbeit: `aihub` Kanban Board

Während hochrangiger Kontext in der Roadmap verbleibt, werden tatsächliche Entwicklungsaufgaben im `aihub` Kanban Board verfolgt. Aufgaben auf diesem Board sind immer mit einem entsprechenden Element in der `aihub-roadmap` verknüpft, um die Nachvollziehbarkeit zu gewährleisten.

Das Board verwendet drei primäre Statusspalten: **To Do**, **In Progress** und **Done**. Wenn Sie mit einer Aufgabe beginnen, weisen Sie sie sich selbst zu und verschieben Sie sie von "To Do" nach "In Progress". Nach Abschluss verschieben Sie sie nach "Done".

::: details :clipboard: Kanban Board-Zugriff
**URL**: `https://github.com/orgs/bbvch-ai/projects/2`

**Mit dem Board via CLI interagieren**:

```bash
# List all open issues on the Kanban board that are assigned to you
gh issue list -R "bbvch-ai/aihub-core" -a "@me" -S "project:bbvch-ai/2"

# View the details and comments of a specific issue
gh issue view <issue_number> -c -R "bbvch-ai/aihub-core"
```
:::

### :memo: Architectural Decision Records (ADRs)

Um sicherzustellen, dass sich unsere Architektur konsistent weiterentwickelt, werden alle bedeutenden technischen Entscheidungen mithilfe eines Architectural Decision Record (ADR)-Prozesses dokumentiert.

#### Konsultationsprotokoll

::: danger :stop_sign: Obligatorische Lektüre
Bevor Sie eine "bedeutende Änderung" vornehmen, müssen Sie die bestehenden ADRs im Verzeichnis `aihub_doc/arc42/decisions/` konsultieren, um sicherzustellen, dass Ihre Änderung nicht mit einer früheren Entscheidung in Konflikt steht. Eine bedeutende Änderung umfasst das Hinzufügen grösserer Abhängigkeiten, das Einführen neuer Tools oder die Änderung fundamentaler Architekturmuster.
:::

#### Dokumentationsprotokoll

Wenn Ihre Aufgabe eine neue bedeutende Entscheidung erfordert, müssen Sie diese dokumentieren, indem Sie eine neue ADR-Datei im selben Verzeichnis erstellen.

::: details :memo: ADR-Vorlage
**Benennungskonvention**: `YYYY_MM_DD_short-decision-summary.md`

**Vorlage**: Verwenden Sie die folgende Markdown-Vorlage für die neue ADR-Datei.

```markdown
# Titel der Entscheidung

Ein klarer, prägnanter Titel. Beispiel: "Redis für Caching einführen"

## Kontext

Beschreiben Sie das Problem oder die Situation, die diese Entscheidung notwendig macht. Was ist der technische oder geschäftliche Kontext?

## Entscheidungstreiber

Listen Sie die wichtigsten Faktoren, die Ihre Entscheidung beeinflussen, als Aufzählungspunkte auf. Dies sind die "Warum's".

## Entscheidung

Formulieren Sie Ihre Entscheidung klar und unzweideutig. Beschreiben Sie genau, was Sie zu tun gewählt haben.

## Konsequenzen

Beschreiben Sie die Ergebnisse Ihrer Entscheidung. Listen Sie sowohl positive Ergebnisse als auch mögliche negative Kompromisse auf.
```
:::

---

## 5. :evergreen_tree: Git- & GitHub-Workflow

Dieses Kapitel beschreibt die Regeln und Prozesse für die Quellcodeverwaltung, einschliesslich Branching, Commit-Konventionen und Pull-Request-Verfahren.

### :herb: Branching-Strategie

Um ein sauberes und überschaubares Repository zu pflegen, folgen wir einer einfachen Branching-Strategie.

::: info :herb: Branch-Struktur
- **`main`-Branch**: Dies ist der einzige langlebige Branch, der die stabile, Hauptentwicklungslinie repräsentiert.

- **Feature-Branches**: Alle neuen Arbeiten, einschliesslich Features, Fehlerbehebungen und Wartungsaufgaben, müssen auf kurzlebigen Branches durchgeführt werden. Diese Branches werden vom `main`-Branch erstellt und über einen Pull Request zurück in den `main`-Branch gemergt. Branch-Namen **müssen** diesem Muster folgen:

  - `type/short-description`

  Wobei `type` eines von `feat`, `fix`, `chore`, `test` oder `doc` sein muss.

  - Beispiel Feature-Branch: `feat/new-agent-workflow`
  - Beispiel Fix-Branch: `fix/login-bug-incorrect-redirect`
:::

### :label: Konventionelle Commits & Pull Request (PR)-Titel

Sowohl Commit-Nachrichten als auch Pull Request (PR)-Titel **müssen** der
[Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/)-Spezifikation folgen. Dies gewährleistet eine klare und
beschreibende Historie, die leicht analysiert werden kann.

Das Format ist: `<type>(<scope>): <subject>`

::: details :label: Formatspezifikation
- **`type`**: Muss eines der folgenden sein: `fix`, `feat`, `test`, `doc`, `chore`.
- **`scope`**: Beschreibt, welcher Teil der Codebasis betroffen ist, z.B. ein Paketname, Kunde oder eine Initiative (z.B.
  `aihub`, `api`, `bbv`).
- **`subject`**: Eine kurze Beschreibung der Änderung im Imperativ.
:::

::: tip :memo: Beispiele
- `fix(aihub): Fix bug where old messages can't be edited anymore`
- `feat(ci-cd): Add new feature to ci-cd pipeline`
:::

### :computer: GitHub CLI Integration

Alle GitHub-bezogenen Operationen sollten mit dem GitHub CLI (`gh`)-Tool statt über die Weboberfläche durchgeführt werden. Dies gewährleistet Konsistenz und ermöglicht Automatisierung.

::: details :computer: Gängige GitHub CLI-Befehle
**Einen Pull Request erstellen**:

```bash
# Create a new PR with a title and body
gh pr create --title "feat(api): Add new endpoint for user profiles" --body "This PR introduces..."
```

**Pull Requests anzeigen**:

```bash
# See the current status of all PRs in the repository
gh pr status

# List all PRs that you have authored
gh pr list --author "@me"
```

**Einen Pull Request überprüfen**:

```bash
# Check out a PR locally to test it
gh pr checkout <pr_number>

# View the details and changes of a PR in the terminal
gh pr view <pr_number> --web

# Approve a PR
gh pr review <pr_number> --approve --body "LGTM!"
```

**Einen Pull Request mergen**:

```bash
# Merge a PR after it has been approved and all checks have passed
gh pr merge <pr_number> --squash
```
:::

### :lock: Branch-Schutzregeln

::: warning :shield: Geschützter Branch
Um die Stabilität und Integrität unserer Codebasis zu gewährleisten, ist der `main`-Branch durch die folgenden Regeln geschützt.
:::

::: details :shield: Schutzregeln
- **Pull Request vor dem Mergen erforderlich**: Alle Änderungen müssen über einen Pull Request erfolgen. Direkte Pushes auf den `main`-Branch sind blockiert.
  - **Erforderliche Genehmigungen**: Mindestens **eine** genehmigende Überprüfung ist vor dem Mergen erforderlich.
  - **Veraltete Genehmigungen verwerfen**: Wenn neue Commits in den Branch gepusht werden, werden frühere Genehmigungen verworfen und eine neue Überprüfung ist erforderlich.
  - **Konversationsauflösung erforderlich**: Alle Kommentare und Diskussionen im PR müssen vor dem Mergen gelöst werden.
- **Lineare Historie erforderlich**: Diese Regel untersagt Merge-Commits und hält die Repository-Historie sauber und leicht nachvollziehbar.
- **Zulässige Merge-Methode**: Nur **Squash Merging** ist aktiviert. Das bedeutet, dass alle Commits eines Feature-Branches zu einem einzigen Commit zusammengeführt werden, wenn sie in den `main`-Branch gemergt werden. Dies hält die Historie des `main`-Branches prägnant und linear.
- **Force Pushes und Löschungen blockieren**: Force-Pushing auf den `main`-Branch ist untersagt, um die Commit-Historie zu erhalten. Das Löschen des `main`-Branches ist ebenfalls eingeschränkt.
:::

---

## 6. :test_tube: Tests im Detail

Dieses Kapitel beschreibt die Test-Frameworks und Philosophien, die im AI-Hub-Projekt verwendet werden. Während umfassendes Testen ein Kernbestandteil unseres Entwicklungszyklus ist, folgen wir **nicht** einer strikten Test-Driven Development (TDD)-Methodologie.

### :checkered_flag: Pytest & Marker

::: info :test_tube: Test-Struktur
**`pytest`** ist das Standard-Test-Framework für das AI-Hub-Projekt. Tests befinden sich in einem `tests`-Verzeichnis auf derselben Ebene wie der zu testende Code. Alle Testdateien müssen mit `test_` beginnen, z.B. `test_<zu_testende_einheit>.py`.
:::

::: info :label: Test-Marker
Um Tests besser zu kategorisieren, verwenden wir `pytest`-Marker. Dies ermöglicht es uns, bestimmte Testtypen selektiv auszuführen oder auszuschliessen. Gängige Marker sind:

- `azure`
- `self_hosted`
- `slow`
- `integration`
:::

### :cucumber: Verhaltensgesteuerte Entwicklung (BDD) mit pytest-bdd

Für das Testen von Agenten- und Prozess-Workflows versuchen wir, die **verhaltensgesteuerte Entwicklung (BDD)** mit dem `pytest-bdd`-Plugin zu nutzen. BDD bietet eine strukturierte Methode, um Tests zu schreiben, die sowohl für technische als auch für nicht-technische Teammitglieder leicht verständlich sind.

::: warning :warning: Async-Test-Einschränkung
Allerdings unterstützt `pytest-bdd` asynchrones Testen nicht vollständig, was umständlich sein kann. Daher greifen wir für wirklich asynchrone Tests oft auf die direkte Verwendung von **`pytest`** zurück.
:::

::: details :gear: Funktionsweise
Der BDD-Prozess umfasst zwei Hauptkomponenten:

1. **Feature-Dateien**: Diese Dateien, geschrieben in Gherkin-Syntax (`.feature`), beschreiben ein Feature und dessen Szenarien in einfachem Englisch. Sie befinden sich im Verzeichnis `tests/features/`.
2. **Schrittdefinitionen**: Dies sind Python-Funktionen, die die in den Feature-Dateien definierten Schritte implementieren. Sie verwenden Dekoratoren wie `@given`, `@when` und `@then`, um den Code mit den Gherkin-Schritten zu verknüpfen.

Tests sind in drei Teile gegliedert: `Given` (Einrichtung), `When` (Ausführung) und `Then` (Behauptung).
:::

::: tip :bulb: Warum wir BDD verwenden
Wenn möglich, bevorzugen wir BDD aus mehreren wichtigen Gründen:

- **Lesbare Tests**: In einfacher Sprache geschriebene Szenarien ermöglichen es nicht-technischen Stakeholdern, Anforderungen zu validieren.
- **Wiederverwendbarkeit**: Schrittdefinitionen können über mehrere Szenarien hinweg geteilt werden, was die Code-Duplizierung reduziert.
- **Schnellere Iterationen**: Neue Testfälle können oft durch das Schreiben neuer Gherkin-Szenarien hinzugefügt werden, ohne neuen Python-Code zu benötigen.
- **Engere Zusammenarbeit**: Der Prozess fördert die Zusammenarbeit zwischen Geschäfts-, QA- und Entwicklungsteams.
:::

---

## 7. :pencil2: Code-Konventionen

Die Einhaltung eines konsistenten Codierungsstandards ist entscheidend für die Aufrechterhaltung der Qualität, Lesbarkeit und langfristigen Wartbarkeit der AI-Hub-Codebasis. Die folgenden Konventionen sind nicht optional; sie werden von unseren CI/CD-Pipelines strikt durchgesetzt.

### :art: Formatierung, Linting und Typ-Prüfung

Wir verwenden eine spezifische Reihe von Tools, um die Code-Formatierung zu automatisieren, Stilregeln durchzusetzen und statische Analysen durchzuführen.

::: details :black_circle: Code-Formatter: Black
**Regel**: Der gesamte Python-Code wird mit dem `black` Code-Formatter formatiert. **Konfiguration**: Die Zeilenlänge ist auf **120 Zeichen** eingestellt. Keine andere Konfiguration wird vom Standard geändert.
:::

::: details :zap: Linter: Ruff
**Regel**: Wir verwenden `ruff` für Hochleistungs-Linting und Import-Sortierung. **Konfiguration**: Wir erzwingen eine spezifische Reihe von Regeln: `select = ["E", "F", "UP", "I"]`.

- `E`/`F`: Fängt Fehler und Warnungen von Pyflakes ab (z.B. ungenutzte Imports, undefinierte Namen).
- `UP`: Enthält Regeln von `pyupgrade` zur Durchsetzung moderner Python-Syntax.
- `I`: Erzwingt die Import-Sortierung, die automatisch von Ruff gehandhabt wird.
:::

::: details :mag: Statische Typ-Prüfung: MyPy
**Regel**: Wir verwenden `mypy` für die statische Typ-Prüfung, um Typ-bezogene Fehler vor der Laufzeit abzufangen. **Konfiguration**: Die Typ-Prüfung wird im Modus `strict = true` ausgeführt, der das höchste Mass an Typensicherheit erzwingt.
:::

### :hammer: Durchsetzung via Makefile

::: danger :rotating_light: Kritische Befehle
Während diese Prüfungen automatisch in unserer CI-Pipeline ausgeführt werden, müssen Sie sie **unbedingt** lokal ausführen, bevor Sie Ihren Code committen. Jeder Scope (und das Stammverzeichnis) enthält ein `Makefile` mit den notwendigen Befehlen. Führen Sie diese immer innerhalb einer aktivierten Poetry-Shell aus.

- `make format`: Formatiert den gesamten Code im aktuellen Scope mit **Black**.
- `make lint`: Lintet den gesamten Code mit **Ruff** und führt **MyPy** zur Typ-Prüfung aus.
- `make pr-ready`: Dies ist der **wichtigste Befehl**. Er führt sowohl `make format` als auch `make lint` mit Auto-Fixing-Funktionen (`ruff check --fix`) aus. Führen Sie diesen Befehl aus, um sicherzustellen, dass Ihr Code zu 100 % konform ist, bevor Sie einen Pull Request erstellen.
:::

### :abc: Namenskonventionen

::: info :snake: Snake-Case-Regeln
- **Dateien und Verzeichnisse**: Alle Python-Dateien und Verzeichnisnamen müssen `snake_case` verwenden.
  - Beispiel Datei: `agent_workflow_manager.py`
  - Beispiel Verzeichnis: `workflow_steps`
- **Testdateien**: Alle Testdateien müssen mit `test_` beginnen und der `snake_case`-Konvention folgen.
  - Beispiel: `test_agent_workflow_manager.py`
:::

::: info :camel: Camel-Case-Regeln
- **Klassen**: Alle Klassennamen müssen `CamelCase` verwenden.
  - Beispiel: `AgentWorkflowManager.py`, `ProcessExecutor.py`, `UserIdentity.py`
:::

### :speech_balloon: Docstrings und Kommentare

::: tip :speech_balloon: Best Practices für die Dokumentation
**Docstrings**: Alle öffentlichen Module, Klassen, Methoden und Funktionen **müssen** einen mehrzeiligen Docstring haben, der ihren Zweck, Kontext und ihre Verwendung klar erklärt. Dies ist entscheidend für die Wartbarkeit und damit andere Ihren Code verstehen können.

```python
class AgenticProcess:
    """
    Manages the lifecycle of an an agentic process from instantiation to completion.

    This class orchestrates the flow of events between different actors (agents, humans, programs)
    and ensures that the process adheres to its predefined workflow definition.
    """
```

**Kommentare**: Kommentare sollten das **Warum** erklären, nicht das **Was**. Schreiben Sie Ihren Code so selbstdokumentierend wie möglich und verwenden Sie Kommentare nur, um komplexe Logik, Geschäftsregeln oder die Begründung einer spezifischen Implementierungsentscheidung zu klären.

```python
# Incorrect: "what" the code does
# Increment the counter
i += 1

# Correct: "why" the code does it
# We must wait for the event to propagate before proceeding to avoid a race condition.
await asyncio.sleep(0.1)
```
:::

### :label: Typ-Annotationen

Strikte und spezifische Typ-Hinweise sind obligatorisch.

::: tip :label: Richtlinien für Typ-Annotationen
**Regel**: Alle Variablen, Funktionsargumente und Rückgabewerte müssen Typ-Annotationen haben.

**Stil**: Verwenden Sie nach Möglichkeit moderne Standardbibliothekstypen (z.B. `list[int]` anstelle von `typing.List[int]` und `int | None` anstelle von `typing.Optional[int]`).

**Erweiterte Typen**: Für komplexere Szenarien verwenden Sie die erweiterten Typen, die im Modul `typing` verfügbar sind, wie `Annotated`, `TypeVar` und `Generic`.

```python
from typing import Annotated
from fastapi import Depends


# Good example demonstrating modern type hints and advanced usage
async def get_user_data(
        user_id: int | None,
        token: Annotated[str, Depends(oauth2_scheme)]
) -> UserDto:
    """Fetches user data based on an ID and an authentication token."""
    if user_id is None:
        raise ValueError(...)
    # ... logic to fetch data
    return UserDto(user_id=user_id, name="Example User")
```

**Komplexe Typen**: Vermeiden Sie Dictionaries oder komplexe Typen wie `tuple[str, int, list[float]]` um jeden Preis. Erstellen Sie immer Pydantic-Objekte oder Dataclasses, um komplexe Datenstrukturen zu halten.

**Lassen Sie Dinge fehlschlagen**: Fangen Sie keine Fehler ab und geben Sie kein None zurück. Stattdessen soll eine Funktion oder Methode fehlschlagen, wenn sie ihre Ausgabe nicht erzeugen kann.
:::

---

## 8. :repeat: Der Kernentwicklungszyklus

Dieses Kapitel beschreibt den standardmässigen, schrittweisen Prozess für jede Entwicklungsaufgabe. Die Befolgung dieses Zyklus stellt sicher, dass alle Arbeiten konsistent, kontextbewusst und gemäss unseren Qualitätsstandards ausgeführt werden.

### :mag: Schritt 1: Ziel und Kontext verstehen

::: tip :dart: Beginnen Sie mit dem Kontext
Jede Entwicklungsaufgabe beginnt mit einem klaren Ziel, typischerweise als GitHub-Issue-Nummer bereitgestellt. Sie müssen zuerst die Anforderungen der Aufgabe und ihren Platz innerhalb der umfassenderen Projekt-Roadmap verstehen.
:::

::: info :link: Aufgabenverknüpfung
Der Issue-Titel Ihrer Aufgabe enthält oft ein Präfix in Klammern (z.B. `[process]`), das ihn mit einer grösseren Initiative auf der `aihub-roadmap` verknüpft. Sie können die Roadmap mit dem `gh` CLI anzeigen:
:::

::: tip :mag: Hochrangige Initiativen anzeigen
```bash
gh project item-list 7 --owner bbvch-ai --limit 100
```

Dieser Befehl zeigt die hochrangigen Initiativen an:

```
> Issue  🗺️ Infrastructure [infra]                             375      bbvch-ai/aihub-core  PVTI_lADOCmtSJM4ArqDTzgbcrk4
> Issue  🗺️ Spike Container Deployment [container]             422      bbvch-ai/aihub-core  PVTI_lADOCmtSJM4ArqDTzgcQbYQ
> Issue  🗺️ Agentic Process Automation [process]               442      bbvch-ai/aihub-core  PVTI_lADOCmtSJM4ArqDTzgcTfWw
```

Indem Sie den Haupt-Initiativen-Issue (z.B. #442) abrufen, können Sie mehr Einblick in das Gesamtziel gewinnen und sehen, wie Ihre spezifische Aufgabe zu verwandten Issues passt.

```bash
gh issue view 442 -c -R "bbvch-ai/aihub-core"
```

Dies gibt Ihnen den Kontext und eine Checkliste verwandter Aufgaben, die Ihnen helfen, das Gesamtbild zu verstehen, bevor Sie beginnen.
:::

### :broom: Schritt 2: Arbeitsbereich vorbereiten

Bevor Sie Code schreiben, überprüfen Sie Ihre lokale Umgebung.

::: info :gear: Arbeitsbereichsvorbereitung
1. **Überprüfen Sie Ihren aktuellen Branch**. Wenn Sie sich auf `main` befinden, erstellen Sie einen neuen Branch, der der im Kapitel Git- & GitHub-Workflow beschriebenen Benennungskonvention folgt (z.B. `feat/new-process-feature`).
2. **Überprüfen Sie bestehende Arbeiten**. Wenn Sie sich bereits auf einem Feature-Branch befinden, führen Sie `git diff main...` aus, um zu sehen, welche Änderungen bereits auf diesem Branch vorgenommen wurden.
:::

### :bulb: Schritt 3: Lösung planen und implementieren

::: tip :bulb: Implementierungsschritte
1. **Planen Sie Ihre Implementierung**. Überlegen Sie sich die Änderungen, die Sie vornehmen müssen, bevor Sie Code schreiben.
2. **Wählen Sie den richtigen Scope**. Es ist entscheidend, dass Sie Ihren Code im richtigen Paket platzieren (`aihub_lib`, `aihub_agent`, `aihub_api` usw.). Wenn Code von mehr als einem Dienst verwendet wird, gehört er in `aihub_lib`.
3. **Schreiben Sie den Code**. Während Sie Ihre Lösung implementieren, befolgen Sie strikt alle Regeln, die im Kapitel **Code-Konventionen** definiert sind.
:::

### :white_check_mark: Schritt 4: Codequalität überprüfen

Sobald Sie eine funktionierende Implementierung haben, müssen Sie unsere automatisierten Formatierungs- und Linting-Tools ausführen, um sicherzustellen, dass Ihr Code zu 100 % unseren Standards entspricht.

::: tip :white_check_mark: Qualitätsprüfung
Führen Sie innerhalb der aktivierten Poetry-Shell des Scopes, an dem Sie gearbeitet haben, Folgendes aus:

```bash
make pr-ready
```

Dieser Befehl formatiert Ihren Code automatisch und meldet alle Linting- oder Typfehler, die behoben werden müssen.
:::

### :test_tube: Schritt 5: Tests schreiben und ausführen

Unser Ansatz zum Testen ist pragmatisch.

::: tip :test_tube: Pragmatischer Testansatz
- **Neue Tests schreiben**: Sie sind nicht verpflichtet, für jede Änderung Tests zu schreiben, da wir keine 100%ige Testabdeckung anstreben. Wenn es jedoch einfach und unkompliziert ist, einen Test für Ihren neuen Code zu schreiben, sollten Sie dies tun. Schreiben Sie komplexe Tests nur, wenn Sie ausdrücklich dazu aufgefordert werden.
- **Alle Tests ausführen**: Unabhängig davon, ob Sie einen neuen Test geschrieben haben oder nicht, müssen Sie die gesamte lokale Testsuite ausführen, um sicherzustellen, dass Ihre Änderungen keine bestehende Funktionalität beschädigt haben. Tests müssen immer bestanden werden, bevor Sie Ihre Arbeit als abgeschlossen betrachten.
:::

::: tip :test_tube: Tests ausführen
Um die lokale Testsuite auszuführen, verwenden Sie den Befehl:

```bash
make test
```
:::

---

## 9. :books: Dokumentation und Selbstverbesserung

Ein Schlüsselprinzip des AI-Hub-Projekts ist, dass die Dokumentation mit dem Code wachsen muss. Dieses Kapitel beschreibt unsere Dokumentationsphilosophie und den Prozess, den jeder Entwickler befolgen muss, um sicherzustellen, dass unsere Dokumentation präzise, hilfreich und aktuell bleibt.

### :thought_balloon: Dokumentationsphilosophie

Wir folgen einem **README.md-only** Dokumentationsprinzip. Die gesamte Projektdokumentation befindet sich an einem von zwei Orten:

::: info :two: Zwei Dokumentationstypen
1. **Code-Docstrings**: Für Dokumentation, die spezifisch für eine einzelne Klasse, Methode oder Funktion ist, verwenden wir detaillierte Docstrings direkt in der Implementierungsdatei. Dies ist die häufigste Form der Dokumentation.
2. **README.md-Dateien**: Für Dokumentation, die für einen grösseren Teil der Codebasis (einen spezifischen Ordner, einen Scope oder das gesamte Projekt) gilt, verwenden wir `README.md`-Dateien.
:::

::: tip :file_folder: Hierarchische Struktur
Diese README-Dateien sind hierarchisch. Eine `README.md` kann im Projekt-Root, innerhalb jedes Scopes (z.B. `aihub_agent/README.md`) oder sogar in verschachtelten Unterordnern existieren. Dies ermöglicht es uns, Kontext auf der am besten geeigneten Ebene bereitzustellen.

Es ist entscheidend, dass diese Dateien aktuell und gut geschrieben sind, da wir sie verwenden, um automatisch eine Entwickler-Dokumentationsseite mit VuePress zu generieren.
:::

### :arrows_clockwise: Das Selbstverbesserungsprotokoll

::: danger :warning: Obligatorischer Schritt
Dies ist der letzte, entscheidende Schritt des Entwicklungszyklus. Bevor Sie eine Aufgabe als abgeschlossen betrachten, müssen Sie **unbedingt** Ihre Arbeit und deren Auswirkungen auf die Dokumentation reflektieren. Dies ist nicht optional; es ist wesentlich für die langfristige Gesundheit des Projekts.
:::

::: details :question: Fragen zur Selbstreflexion
Nach der Implementierung Ihrer Änderungen stellen Sie sich die folgenden Fragen:

- **Macht meine Änderung bestehende Dokumentation ungenau?** Wenn Ihre Codeänderung impliziert, dass ein Abschnitt in einer `README.md` nun veraltet oder falsch ist, müssen Sie diesen Abschnitt des README an Ihre Änderungen anpassen.

- **Fehlt Information, die mir geholfen hätte?** Wenn Sie wichtige Informationen selbst entdecken mussten, die nicht dokumentiert waren, müssen Sie diese hinzufügen. Erweitern Sie entweder eine bestehende `README.md` oder erstellen Sie eine neue auf der entsprechenden Ebene (Ordner, Scope), um dieses Wissen zu teilen.

- **Konfliktierte die Dokumentation mit dem Code?** Wenn Sie Informationen in einer `README.md` gefunden haben, die falsch waren, müssen Sie diese korrigieren oder entfernen. In diesem Projekt ist der **Code immer die letztgültige Wahrheit.**
:::

---

## 10. :book: Technische Referenz

Dieses Kapitel bietet eine Referenz für die Paketmanagementstrategie des Projekts und die im Stack verwendeten Technologien.

### :package: Paketmanagement & Versionierung

::: details :package: Paketstruktur
Der AI-Hub besteht aus mehreren Paketen, die spezifische Funktionalitäten handhaben:

- `aihub_agent`: Enthält gemeinsamen Code für die Agentenentwicklung.
- `aihub_api`: Enthält gemeinsamen Code für die API-Implementierung.
- `aihub_bot`: Enthält gemeinsamen Code für die Bot-Entwicklung.
- `aihub_pipeline`: Enthält gemeinsamen Code für die Pipeline-Entwicklung.
- `aihub_process`: Enthält gemeinsamen Code für die Prozessentwicklung.
- `aihub_lib`: Eine grundlegende Bibliothek, die Code enthält, der für mehrere andere Pakete relevant ist. Das `aihub_lib`-Paket wird von allen anderen Paketen verwendet.
:::

::: tip :label: Versionierung und Referenzierung
Alle Pakete haben Versionen, die synchron mit den Tags im Repository erhöht werden. Das bedeutet, dass die Version eines Pakets bei jedem Merge in den Main-Branch aktualisiert wird.

Standardmässig referenzieren Pakete `aihub_lib` über seine Git-URL in der Datei `pyproject.toml`, wodurch die Versionierung über Git-Tags gehandhabt werden kann. Für die lokale Entwicklung ist es möglich, auf eine lokale Version der Core-Bibliothek zu wechseln, indem der Befehl `make use-local-core` ausgeführt wird. Für die Bereitstellung wird die Referenz zurück zum GitHub-Repository gewechselt, wobei die Version über ihren Tag spezifiziert wird.
:::
