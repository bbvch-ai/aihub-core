---
title: Einrichtung der Entwicklungsumgebung
source_sha: "8d36d7aeab4d3bcc6d16bd8738c61c79e2ef7c121277841d25f1730b0248d2d4"
---

[@mhoegger](https://github.com/mhoegger)

# Einrichtung der Entwicklungsumgebung: Ihre ersten 15 Minuten mit dem SDK

Der Einstieg in das Swiss AI Hub SDK ist unkompliziert. Innerhalb von 15 Minuten verfügen Sie über eine vollständige Entwicklungsumgebung, in der Ihr erster benutzerdefinierter Agent echte Anfragen verarbeitet.

## Voraussetzungsprüfung

Bevor wir beginnen, stellen Sie sicher, dass Sie diese Tools installiert haben:

**Erforderliche Tools:**

- **Python 3.13** – Das SDK benötigt Python 3.13 für alle Komponenten
- **uv** – Für Abhängigkeitsmanagement und virtuelle Umgebungen
- **Docker & Docker Compose** – Zum Betrieb der Plattforminfrastruktur
- **make** – Zum Ausführen gängiger Entwicklungsbefehle

**Optional, aber hilfreich:**

- **Node.js LTS + pnpm** – Nur für die Anpassung des Frontends erforderlich
- **Postman** – Für API-Tests und -Erkundung
- **MongoDB Compass** – Für die Datenbankinspektion während der Entwicklung

::: tip Schnelle Installationsprüfung
Überprüfen Sie Ihr Setup mit diesen Befehlen:

```bash
python --version    # Should show 3.13.x
uv --version        # Any recent version
docker --version    # Any recent version
make --version      # Any version
```
:::

## Projekteinrichtung: 3 Minuten

### Schritt 1: Erstellen Sie Ihre Projektstruktur

Erstellen Sie ein neues Python-Projekt und öffnen Sie ein Terminal im Stammverzeichnis dieses Projekts.

Initialisieren Sie ein neues uv-Projekt:

```bash
uv init
```

### Schritt 2: Installieren Sie die Swiss AI Hub CLI

Das CLI-Tool automatisiert die meisten Einrichtungsschritte:

```bash
uv add --dev swiss-ai-hub-cli
```

### Schritt 3: Generieren Sie die Plattforminfrastruktur

Erstellen Sie den Entwicklungsinfrastruktur-Stack:

```bash
uv run swiss-ai-hub generate-compose
```

Dies erstellt `docker-compose.platform.dev.yml` mit allen Services, die Sie benötigen: NATS-Messaging, MongoDB, Redis, Vektordatenbanken und die Swiss AI Hub Plattformkomponenten.

### Schritt 4: Umgebung konfigurieren

Generieren Sie die Umgebungskonfiguration:

```bash
uv run swiss-ai-hub generate-env
```

Dies erstellt `.env` mit sinnvollen Standardeinstellungen. Sie sehen Platzhalterwerte für die OAuth2-Konfiguration – wir verwenden vorerst den Entwicklungsmodus, daher können Sie diese für erste Tests unverändert lassen.

## Plattform starten: 5 Minuten

Starten Sie die vollständige Swiss AI Hub Plattform:

```bash
docker compose -f infra/docker-compose.dev.yml --env-file .env up -d
```

Warten Sie, bis alle Services gestartet sind (beobachten Sie die Logs mit `docker compose logs -f`, wenn Sie den Startvorgang sehen möchten).

**Überprüfen Sie, ob die Plattform läuft:**

- Öffnen Sie `http://localhost:8080` – Sie sollten die Swiss AI Hub Weboberfläche sehen
- Sie werden feststellen, dass noch keine Agents verfügbar sind – das ist zu erwarten!

::: warning Häufiges Startproblem
Sollten Services nicht starten, überprüfen Sie, ob die Ports 8080, 27017, 6379 und 4222 nicht bereits auf Ihrem System verwendet werden.
:::

## Erstellen Sie Ihren ersten Agent: 5 Minuten

### Schritt 1: Generieren Sie das Agent-Gerüst

Erstellen Sie Ihren ersten benutzerdefinierten Agenten:

```bash
uv run swiss-ai-hub new-agent my_custom_agent
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

### Schritt 2: Untersuchen Sie den generierten Agenten

Sehen Sie sich den generierten Agent-Code in `agents/my_custom_agent/MyCustomAgent/MyCustomAgent.py` an:

```python
# TODO: tbd
```

Dieser Agent demonstriert die Kernmuster des SDK:

- **Ereignisgesteuerte Schritte** mit streng typisierten Eingaben und Ausgaben
- **Automatische Plattformintegration** für Authentifizierung, Tracing und Monitoring
- **Einfache Geschäftslogik**, die Sie an Ihre Bedürfnisse anpassen können

### Schritt 3: Starten Sie Ihren Agenten

Generieren Sie eine Docker-Compose-Datei, die Ihren Agenten enthält:

```bash
uv run swiss-ai-hub generate-agent-compose --with-agent my_custom_agent
```

Dies erstellt `docker-compose-agents.dev.yml` mit Ihrem Agenten, der für die Entwicklung konfiguriert ist (Hot Reload inbegriffen).

Erstellen Sie eine grundlegende `.env`-Datei für die Agent-Konfiguration:

Starten Sie alles zusammen:

```bash
docker compose \
  -f infra/docker-compose.dev.yml \
  -f docker-compose-agents.dev.yml \
  --env-file .env \
  up -d
```

## Testen Sie Ihren Erfolg: 2 Minuten

### Schritt 1: Überprüfen Sie die Agent-Registrierung

Überprüfen Sie die Weboberfläche unter `http://localhost:8080`. Sie sollten nun Ihren `my_custom_agent` Agenten in den Agents aufgeführt sehen, und er wird als `online` angezeigt.

### Schritt 2: Testen Sie die Agent-Interaktion

Klicken Sie auf Ihren Agenten und senden Sie eine Testnachricht. Sie sollten eine Antwort erhalten, die zeigt, dass Ihr Agent die Anfrage verarbeitet hat.

### Schritt 3: Beobachten Sie das Agent-Verhalten

Besuchen Sie `http://localhost:6006`, um das Langfuse-Tracing zu sehen. Sie sehen detaillierte Traces der Ausführung Ihres Agenten, die jeden Schritt sowie dessen Ein- und Ausgaben zeigen.

## Was ist gerade passiert?

In 15 Minuten haben Sie etwas Bemerkenswertes erreicht:

**Komplette KI-Plattform:** Sie betreiben eine vollständige Enterprise-KI-Plattform mit Authentifizierung, Monitoring, Kostenverfolgung und Observability.

**Benutzerdefinierte Agent-Integration:** Ihr benutzerdefinierter Agent erbt automatisch alle Plattformfunktionen – er erscheint in der Web-UI, verarbeitet Anfragen und verfolgt seine Ausführung ohne zusätzliche Konfiguration.

**Entwicklungsbereite Umgebung:** Das Hot-Reload-Setup bedeutet, dass Sie Ihren Agent-Code ändern und Änderungen sofort sehen können, ohne Container neu erstellen zu müssen.
