---
title: Einrichtung der Entwicklungsumgebung
source_sha: fa75c93382046390f7b813336ded32ec79fc2f521e8231c3014ba979d4fb8d98
---

# Einrichtung der Entwicklungsumgebung

Diese Seite führt Sie von einer frischen Windows-Maschine zu einem laufenden Swiss AI Hub Development Stack. Die
Infrastruktur (Datenbanken, NATS, Keycloak, LiteLLM, Milvus, SeaweedFS, Langfuse und Verwandte) läuft in Docker; der
Code, an dem Sie tatsächlich arbeiten, läuft mit Hot Reload aus Ihrem Checkout auf dem Host. Sie ändern eine
Python-Datei und die API startet neu, Sie ändern eine Vue-Komponente und der Browser aktualisiert sich, und nichts wird
dafür in ein Image gebaut.

Die Referenzumgebung ist Ubuntu unter WSL2 mit Docker Desktop, weil das Team überwiegend darauf entwickelt. Alles ab
[Toolchain installieren](#schritt-3-toolchain-installieren) ist reines Linux und funktioniert auf einem nativen
Ubuntu-Rechner oder unter macOS identisch.

## Schritt 1: Ubuntu unter WSL2 installieren

Öffnen Sie PowerShell als Administrator und installieren Sie eine Distribution:

```powershell
wsl --install -d Ubuntu-24.04
```

Starten Sie bei Aufforderung neu und legen Sie anschliessend Ihren Linux-Benutzernamen und Ihr Passwort fest, sobald
sich die Ubuntu-Konsole öffnet. Prüfen Sie, dass Sie WSL Version 2 verwenden:

```powershell
wsl --list --verbose
```

Die Spalte `VERSION` muss `2` anzeigen. WSL 1 kann die Engine-Integration von Docker Desktop nicht ausführen.

::: warning Das Repository im Linux-Dateisystem halten
Klonen Sie in Ihr Linux-Home-Verzeichnis (`~/projects/aihub-core`), niemals in einen Windows-Pfad unterhalb von
`/mnt/c`. Dateisystemübergreifende I/O über `/mnt` ist rund eine Grössenordnung langsamer, und inotify-Events werden
nicht weitergereicht. Dadurch kriecht `uv sync` und Hot Reload funktioniert sowohl für die API als auch für das Admin UI
stillschweigend nicht mehr.
:::

WSL beansprucht standardmässig die Hälfte Ihres Host-RAM, was für einen Stack mit einem Bedarf von 32 GB nicht
ausreicht. Legen Sie auf der Windows-Seite `C:\Users\<you>\.wslconfig` an:

```ini
[wsl2]
memory=32GB
processors=8
swap=16GB
```

Übernehmen Sie die Änderung mit `wsl --shutdown` in PowerShell und öffnen Sie Ubuntu danach erneut.

## Schritt 2: WSL-Backend in Docker Desktop aktivieren

Installieren Sie [Docker Desktop für Windows](https://docs.docker.com/desktop/install/windows-install/) und öffnen Sie
dann dessen Einstellungen:

1. **General** — aktivieren Sie *Use the WSL 2 based engine*.
2. **Resources → WSL integration** — aktivieren Sie *Enable integration with my default WSL distro* oder wählen Sie Ihre
   Ubuntu-Distribution in der Liste darunter explizit aus.
3. **Resources → Network** — aktivieren Sie *Enable host networking*.

Der dritte Punkt ist nicht optional. Der Container `open-webui` läuft mit `network_mode: host`, damit er die API und den
OTEL Collector auf localhost erreicht. Ohne aktiviertes Host Networking kann dieser Container nicht binden und das Chat
UI auf Port 8080 kommt nie hoch, während alle anderen Services gesund aussehen.

Prüfen Sie das aus der Ubuntu-Shell heraus, nicht aus PowerShell:

```bash
docker --version
docker compose version
docker run --rm hello-world
```

Wird `docker` unter Ubuntu nicht gefunden, hat der Schalter für die WSL-Integration nicht gegriffen; starten Sie Docker
Desktop neu und prüfen Sie, ob die Distribution aufgeführt ist.

## Schritt 3: Toolchain installieren

Alles Folgende läuft innerhalb von Ubuntu.

```bash
sudo apt update
sudo apt install -y build-essential git curl make
```

Installieren Sie [uv](https://docs.astral.sh/uv/). Das Tool verwaltet sowohl die virtuelle Umgebung als auch den
Python-3.13-Interpreter, auf den der Workspace gepinnt ist:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc
```

Installieren Sie Node.js 22 oder neuer und aktivieren Sie pnpm über corepack. Die Frontends und die Dokumentations-Site
benötigen das, die Python-Pakete nicht.

```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/master/install.sh | bash
source ~/.bashrc
nvm install 22
corepack enable
```

Prüfen Sie das Ergebnis:

```bash
uv --version
node --version     # v22.x or newer
pnpm --version     # 10.x
make --version
docker compose version
```

Python müssen Sie nicht selbst installieren. `uv sync` lädt den Interpreter herunter, den
`requires-python = ">=3.13, <3.14"` verlangt.

## Schritt 4: Klonen und Bootstrap

```bash
git clone https://github.com/bbvch-ai/aihub-core.git ~/projects/aihub-core
cd ~/projects/aihub-core
make setup-all
```

`make setup-all` erledigt zweierlei: `make setup` löst alle Workspace-Pakete mit `uv sync --all-packages` auf und
kopiert `.env.dev` nach `.env`, sofern noch keine `.env` existiert, und `make setup-frontend` installiert die
Frontend-Abhängigkeiten mit pnpm. Führen Sie die beiden einzeln aus, wenn Sie nur eine Hälfte benötigen.

Die erzeugte `.env` ist eine vollständige, funktionierende Entwicklungskonfiguration. Jedes Secret darin ist ein
bekannter Dev-Wert, und die Swiss LLM Cloud Endpoints sind die einzigen Einträge, die Sie für echten Modellzugriff
ergänzen sollten.

::: danger Ausschliesslich Entwicklungs-Zugangsdaten
`.env.dev` enthält fest hinterlegte Passwörter, Signing Keys und API-Tokens, die im Repository öffentlich sind, darunter
`SUPERUSER_PASSWORD='admin'`. Auf Ihrer Maschine ist das in Ordnung und anderswo unbrauchbar. Kopieren Sie die Datei
niemals auf einen geteilten oder aus dem Internet erreichbaren Host.
:::

## Schritt 5: Infrastruktur starten

```bash
make up-dev
```

Das entspricht `docker compose -f infra/docker-compose.dev.yml --env-file .env up -d --build` und startet rund 30
Container. Der erste Durchlauf lädt mehrere Gigabyte an Images und dauert entsprechend; Milvus, Keycloak und Langfuse
benötigen danach noch ein bis zwei Minuten, bis sie gesund melden.

Beobachten Sie, wie sich der Stack einpendelt:

```bash
docker compose -f infra/docker-compose.dev.yml ps
docker compose -f infra/docker-compose.dev.yml logs -f keycloak
```

Sobald alles läuft, sind diese Dienste auf localhost veröffentlicht. Einträge mit dem Präfix `http://` öffnen sich im
Browser, die übrigen sind Service-Endpoints für Clients und Tooling.

| Service    | URL / Port              | Was es ist                      |
| ---------- | ----------------------- | ------------------------------- |
| OpenWebUI  | `http://localhost:8080` | Chat-Oberfläche                 |
| Keycloak   | `http://localhost:8180` | Identity Provider (Realm aihub) |
| Langfuse   | `http://localhost:6006` | LLM-Tracing und Kostenerfassung |
| Attu       | `http://localhost:3003` | Milvus Admin UI                 |
| SeaweedFS  | `http://localhost:8889` | Filer UI (S3 Gateway auf 9000)  |
| LiteLLM    | `localhost:4000`        | LLM Gateway                     |
| NATS       | `localhost:4222`        | Event-Backbone                  |
| Milvus     | `localhost:19530`       | Vektordatenbank                 |
| FerretDB   | `localhost:27017`       | Dokumentenspeicher              |
| PostgreSQL | `localhost:5432`        | Relationaler Speicher           |
| Valkey     | `localhost:6379`        | Agent-State                     |
| Neo4j      | `http://localhost:7474` | Graph-basiertes Memory          |
| MinerU     | `localhost:8002`        | Dokumenten-Parsing              |

Mit `make down-dev` stoppen Sie den Stack wieder, wenn Sie für den Tag fertig sind.

## Schritt 6: Nur die benötigten Prozesse starten

Die Container oben decken die Infrastruktur ab. Welche Anwendungsprozesse Sie darüber hinaus starten, hängt davon ab,
woran Sie arbeiten, und alle gleichzeitig laufen zu lassen ist selten sinnvoll. Jeder Prozess benötigt ein eigenes
Terminal, und alle folgenden Befehle werden aus dem Repository-Root ausgeführt.

| Arbeit an                  | Starten                                  | Erreichbar unter              |
| -------------------------- | ---------------------------------------- | ----------------------------- |
| Admin UI oder REST API     | API + Admin UI                           | `:8000`, `:3333`              |
| Mandantenverwaltung        | Sysadmin API + Sysadmin UI               | `:8001`, `:3334`              |
| Einem Agent                | API + der Agent + ein UI zur Interaktion | `:8000`, `:3333` oder `:8080` |
| Document Ingestion         | Pipeline                                 | `:3000`                       |
| Dieser Dokumentations-Site | Docs Dev Server, sonst nichts            | `:5173`                       |

### Admin UI und REST API

```bash
cd packages/api && make run-dev
```

```bash
cd packages/web && pnpm dev
```

Uvicorn mit `--reload` auf Port 8000 (OpenAPI-Dokumentation unter `http://localhost:8000/docs`) und Nuxt auf Port 3333.
Der Nuxt Dev Server leitet `/api/v1` per Proxy an `localhost:8000` weiter, die API muss also laufen, sonst schlägt jeder
Request aus dem UI fehl. Der Port und der Pfad zur `.env` im Repository-Root sind im `dev`-Skript bereits hinterlegt,
weitere Flags sind nicht nötig.

### Sysadmin UI und API

```bash
cd packages/sysadmin-api && make run-dev
```

```bash
cd packages/sysadmin-web && pnpm dev
```

Die Sysadmin-Ebene ist ein eigenes Deploy-Artefakt und läuft auf eigenen Ports: die API auf 8001 und das UI auf 3334.
`packages/sysadmin-web` ist ein Nuxt Layer über `packages/web`, leitet `/api/v1` aber an `localhost:8001` weiter und
benötigt damit die Sysadmin API und nicht die Haupt-API. Für die Arbeit an Mandanten, Rollen und Benutzern müssen weder
die Haupt-API noch das Admin UI laufen.

### Agents

```bash
cd packages/agent && make run-rag-agent
```

Der Agent abonniert NATS und registriert sich bei der Plattform. `packages/agent/Makefile` enthält für jeden Agent in
`packages/agent/app/` ein eigenes `run-*`-Target, Sie können also nach Bedarf auf `run-retrieval-agent` oder
`run-llm-wrapping-agent` wechseln.

Der Agent selbst benötigt nur die Docker-Infrastruktur. Um ihm tatsächlich eine Nachricht zu schicken, brauchen Sie
zusätzlich die API sowie entweder das Admin UI auf 3333 oder OpenWebUI auf 8080.

### Document Ingestion Pipelines

```bash
make -C packages/pipeline document-ingestion-pipeline
```

Dagster auf Port 3000. Das Target lädt `.env`, richtet `DAGSTER_HOME` auf `~/.dagster_home` aus und installiert beim
ersten Lauf `dagster.local.yaml` dorthin, damit Ihre Run-Historie Neustarts übersteht. `make playground` und
`make -C packages/pipeline quickstart` starten stattdessen die SDK-Beispiel-Pipelines, falls Sie das suchen.

Kombinieren Sie das mit einem RAG-Agent, wenn Sie den vollständigen Retrieval-Loop benötigen: Dokumente über Dagster
aufnehmen und sie anschliessend über den Agent abfragen.

### Dokumentations-Site

```bash
cd docs && pnpm install
```

```bash
cd docs && pnpm run docs:dev
```

VitePress auf Port 5173, die deutschen Seiten liegen unter `/de/`. Das ist der einzige Punkt auf dieser Seite, der weder
den Docker Stack noch `make setup` benötigt: `docs/` ist kein pnpm Workspace Member, bringt eine eigene `pnpm-lock.yaml`
mit und wird aus dem Verzeichnis heraus installiert statt per Filter aus dem Root.

::: tip Die erste Installation ist absichtlich langsam
Der Workspace setzt `minimumReleaseAge`, pnpm verweigert also jedes Paket, das in den letzten sieben Tagen
veröffentlicht wurde. Das ist Supply-Chain-Härtung und keine defekte Lockfile.
:::

## Schritt 7: Anmelden

Öffnen Sie `http://localhost:3333` (oder `http://localhost:3334` für das Sysadmin UI). Sie werden zu Keycloak auf Port
8180 weitergeleitet. Melden Sie sich mit dem Superuser aus `.env` an:

- Benutzername: `admin`
- Passwort: `admin`

Die Authentifizierung läuft in der Entwicklung über das mitgelieferte Keycloak statt über Azure Entra ID, Sie benötigen
also weder einen Azure Tenant noch OAuth-Zugangsdaten. Die Zugangsdaten stammen aus `SUPERUSER_USERNAME` und
`SUPERUSER_PASSWORD` in `.env.dev`, und das Konto trägt die Rollen `AIHubAccess` und `AIHubSysAdmin`, die das Admin UI,
die Sysadmin-Endpoints und OpenWebUI prüfen. Dieselben Zugangsdaten funktionieren überall.

## Setup überprüfen

Prüfen Sie zuerst die Infrastruktur und danach die Prozesse, die Sie gestartet haben:

- `docker compose -f infra/docker-compose.dev.yml ps` zeigt keinen Container im Zustand `exited` oder `unhealthy`.
- `http://localhost:8000/docs` rendert die API-Referenz.
- `http://localhost:3333` meldet Sie an und zeigt das Admin UI.
- `http://localhost:3334` zeigt die Mandantenliste, falls Sie das Sysadmin-Paar gestartet haben.
- Die Agent-Liste im Admin UI enthält den gestarteten Agent und kennzeichnet ihn als `online`.
- Eine Nachricht an diesen Agent aus `http://localhost:8080` erzeugt eine Antwort.
- `http://localhost:6006` zeigt einen Langfuse-Trace für diesen Austausch.

## WSL-Troubleshooting

**Ein Port funktioniert unter Ubuntu, aber nicht im Windows-Browser.** WSL2 leitet localhost automatisch weiter, das
Relay setzt aber gelegentlich aus, nachdem der Host im Standby war. `wsl --shutdown` aus PowerShell behebt das. Bleibt
ein bestimmter Dev-Server unerreichbar, binden Sie ihn stattdessen an alle Interfaces: `pnpm dev --host 0.0.0.0` für
eines der beiden Frontends oder passen Sie das `--host`-Flag im betreffenden Make-Target an.

**OpenWebUI auf 8080 kommt nie hoch, während alles andere gesund ist.** Host Networking ist in Docker Desktop
deaktiviert. Siehe [Schritt 2](#schritt-2-wsl-backend-in-docker-desktop-aktivieren).

**`uv sync` ist langsam und Hot Reload greift nie.** Das Repository liegt auf `/mnt/c`. Verschieben Sie den Klon in das
Linux-Dateisystem; es gibt keine Konfiguration, die den gemounteten Pfad schnell macht.

**Container werden per OOM beendet oder die Maschine friert ein.** WSL ist unterhalb dessen gedeckelt, was der Stack
braucht. Erhöhen Sie `memory` in `.wslconfig` und führen Sie `wsl --shutdown` aus.

**Zertifikats- oder Token-Fehler, nachdem das Notebook aus dem Standby kommt.** Die Uhr von WSL läuft gegenüber dem Host
aus dem Tritt und Keycloak weist die abweichenden Zeitstempel zurück. Führen Sie `sudo hwclock -s` innerhalb von Ubuntu
aus oder starten Sie mit `wsl --shutdown` neu.

**Port-Konflikte beim Start.** Auf der Windows-Seite belegt bereits etwas 8080, 5432, 6379 oder 4222. Finden Sie den
Verursacher mit `netstat -ano | findstr :8080` in PowerShell und stoppen Sie ihn, oder ändern Sie das host-seitige
Port-Mapping in `infra/docker-compose.dev.yml`.

## Nächste Schritte

Wenn der Stack läuft, führt Sie [Ihr erster Agent](../3_your_first_agent/) durch den Bau eines Agents mit dem SDK, und
[Ihre erste Pipeline](../4_your_first_pipeline/) macht dasselbe für die Datenaufnahme.
