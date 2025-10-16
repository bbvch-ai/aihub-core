---
title: Einrichtung der Entwicklungsumgebung
index: 1
source_sha: "a20e613065a1a4c01b3f0377d5ba764b27fc6e09f98c35bbcbf5af6935932fec"
---

[@mhoegger](https://github.com/mhoegger)

# Einrichtung der Entwicklungsumgebung: Ihre ersten 15 Minuten mit dem SDK

Der Einstieg in das Swiss AI Hub SDK ist bewusst unkompliziert gestaltet. In nur 15 Minuten verfügen Sie über eine vollständige
Entwicklungsumgebung, in der Ihr erster benutzerdefinierter Agent echte Anfragen verarbeitet.

## Prüfung der Voraussetzungen

Bevor wir beginnen, stellen Sie sicher, dass Sie die folgenden Tools installiert haben:

**Grundlegende Tools:**

- **Python 3.13** – Das SDK erfordert Python 3.13 für alle Komponenten
- **Poetry** – Für die Abhängigkeitsverwaltung und virtuelle Umgebungen
- **Docker & Docker Compose** – Zum Betrieb der Plattforminfrastruktur
- **make** – Zum Ausführen gängiger Entwicklungsbefehle

**Optional, aber hilfreich:**

- **Node.js LTS + pnpm** – Nur für die Frontend-Anpassung erforderlich
- **Postman** – Für API-Tests und -Erkundungen
- **MongoDB Compass** – Für die Datenbankinspektion während der Entwicklung

::: tip Schneller Installations-Check
Überprüfen Sie Ihre Einrichtung mit diesen Befehlen:

```bash
python --version    # Should show 3.13.x
poetry --version    # Any recent version
docker --version    # Any recent version
make --version      # Any version
```
:::

## Projekt-Setup: 3 Minuten

### Schritt 1: Erstellen Sie Ihre Projektstruktur

Erstellen Sie ein neues Python-Projekt und öffnen Sie ein Terminal im Stammverzeichnis dieses Projekts.

Initialisieren Sie ein neues Poetry-Projekt:

```bash
poetry init --no-interaction
```

### Schritt 2: Installieren Sie die AI-Hub CLI

Das CLI-Tool automatisiert die meisten Einrichtungsaufgaben:

```bash
poetry add --group dev aihub-cli
```

### Schritt 3: Plattforminfrastruktur generieren

Erstellen Sie den Entwicklungsinfrastruktur-Stack:

```bash
poetry run aihub generate-compose
```

Dies erstellt die Datei `docker-compose.platform.dev.yml` mit allen benötigten Services: NATS Messaging, MongoDB, Redis,
Vektordatenbanken und den AI-Hub Plattformkomponenten.

### Schritt 4: Umgebung konfigurieren

Generieren Sie die Umgebungskonfiguration:

```bash
poetry run aihub generate-env
```

Dies erstellt die Datei `.env.core` mit sinnvollen Standardeinstellungen. Sie sehen Platzhalterwerte für die OAuth2-Konfiguration –
wir verwenden vorerst den Entwicklungsmodus, daher können Sie diese für erste Tests unverändert lassen.

## Starten der Plattform: 5 Minuten

Starten Sie die vollständige AI-Hub Plattform:

```bash
docker compose -f docker-compose-platform.dev.yml --env-file .env.core up -d
```

Warten Sie, bis alle Services gestartet sind (beobachten Sie die Logs mit `docker compose logs -f`, wenn Sie den Startvorgang sehen möchten).

**Verifizieren Sie, dass die Plattform läuft:**

- Öffnen Sie `http://localhost:8080` – Sie sollten die AI-Hub Weboberfläche sehen
- Sie werden feststellen, dass noch keine Agents verfügbar sind – das ist normal!

::: warning Häufiges Startproblem
Falls Services nicht starten, überprüfen Sie, ob die Ports 8080, 27017, 6379 und 4222 nicht bereits auf Ihrem System verwendet werden.
:::

## Erstellen Sie Ihren ersten Agent: 5 Minuten

### Schritt 1: Agent-Gerüst generieren

Erstellen Sie Ihren ersten benutzerdefinierten Agent:

```bash
poetry run aihub new-agent my_custom_agent
```

Dies erstellt eine vollständige Agent-Struktur:

```
agents/
├── pyproject.toml              # Shared dependencies
└── my_custom_agent/            # Your agent
    ├── Dockerfile              # Container definition
    ├── main.py                 # Entry point
    └── MyCustomAgent/          # Implementation
        ├── MyCustomAgent.py
        ├── MyCustomAgentConfig.py
        └── events/             # Custom events
```

### Schritt 2: Untersuchen Sie den generierten Agent

Betrachten Sie den generierten Agent-Code in `agents/my_custom_agent/MyCustomAgent/MyCustomAgent.py`:

```python
# TODO: tbd
```

Dieser Agent demonstriert die Kernmuster des SDK:

- **Ereignisgesteuerte Schritte** mit stark typisierten Ein- und Ausgaben
- **Automatische Plattformintegration** für Authentifizierung, Tracing und Überwachung
- **Einfache Geschäftslogik**, die Sie an Ihre Bedürfnisse anpassen können

### Schritt 3: Starten Sie Ihren Agent

Generieren Sie eine Docker Compose-Datei, die Ihren Agent enthält:

```bash
poetry run aihub generate-agent-compose --with-agent my_custom_agent
```

Dies erstellt die Datei `docker-compose-agents.dev.yml` mit Ihrem Agent, der für die Entwicklung konfiguriert ist (Hot Reload inbegriffen).

Erstellen Sie eine grundlegende `.env`-Datei für die Agent-Konfiguration:

Starten Sie alles zusammen:

```bash
docker compose \
  -f docker-compose-platform.dev.yml \
  -f docker-compose-agents.dev.yml \
  --env-file .env.core \
  --env-file .env \
  up -d
```

## Testen Sie Ihren Erfolg: 2 Minuten

### Schritt 1: Agent-Registrierung überprüfen

Überprüfen Sie die Weboberfläche unter `http://localhost:8080`. Sie sollten nun Ihren `my_custom_agent` Agent in den Agents
aufgelistet und als `online` angezeigt sehen.

### Schritt 2: Agent-Interaktion testen

Klicken Sie auf Ihren Agent und senden Sie eine Testnachricht. Sie sollten eine Antwort erhalten, die zeigt, dass Ihr Agent die Anfrage verarbeitet hat.

### Schritt 3: Agent-Verhalten beobachten

Besuchen Sie `http://localhost:6006`, um das Phoenix-Tracing zu sehen. Sie sehen detaillierte Traces der Ausführung Ihres Agents,
die jeden Schritt und seine Ein-/Ausgaben zeigen.

## Was ist gerade passiert?

In 15 Minuten haben Sie etwas Bemerkenswertes erreicht:

**Vollständige KI-Plattform:** Sie betreiben eine vollständige Enterprise-KI-Plattform mit Authentifizierung, Überwachung, Kostenverfolgung
und Observability.

**Benutzerdefinierte Agent-Integration:** Ihr benutzerdefinierter Agent erbt automatisch alle Plattformfunktionen – er erscheint
in der Web-UI, verarbeitet Anfragen und verfolgt seine Ausführung ohne zusätzliche Konfiguration.

**Entwicklungsbereite Umgebung:** Das Hot-Reload-Setup bedeutet, dass Sie Ihren Agent-Code ändern und Änderungen sofort
sehen können, ohne Container neu erstellen zu müssen.
