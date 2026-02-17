---
title: Einrichtung der Entwicklungsumgebung
source_sha: 268d57ac1d8a47b023394bb28f7e7d53bf34eaeffdc378f8ebc246a60ed0c940
---

[@mhoegger](https://github.com/mhoegger)

# Einrichtung der Entwicklungsumgebung: Ihre ersten 15 Minuten mit dem SDK

Der Einstieg in das Swiss AI Hub SDK ist bewusst einfach gestaltet. In 15 Minuten werden Sie eine vollständige
Entwicklungsumgebung in Betrieb haben, in der Ihr erster benutzerdefinierter Agent echte Anfragen verarbeitet.

## Prüfung der Voraussetzungen

Bevor wir beginnen, stellen Sie sicher, dass Sie diese Tools installiert haben:

**Wesentliche Tools:**

- **Python 3.13** - Das SDK erfordert Python 3.13 für alle Komponenten
- **Poetry** - Für das Abhängigkeitsmanagement und virtuelle Umgebungen
- **Docker & Docker Compose** - Zum Betrieb der Plattforminfrastruktur
- **make** - Zum Ausführen gängiger Entwicklungsbefehle

**Optional, aber hilfreich:**

- **Node.js LTS + pnpm** - Nur für die Frontend-Anpassung erforderlich
- **Postman** - Für API-Tests und -Erkundungen
- **MongoDB Compass** - Zur Datenbankinspektion während der Entwicklung

::: tip Schnelle Installationsprüfung
Überprüfen Sie Ihr Setup mit diesen Befehlen:

```bash
python --version    # Should show 3.13.x
poetry --version    # Any recent version
docker --version    # Any recent version
make --version      # Any version
```
:::

## Projekteinrichtung: 3 Minuten

### Schritt 1: Erstellen Sie Ihre Projektstruktur

Erstellen Sie ein neues Python-Projekt und öffnen Sie ein Terminal im Stammverzeichnis dieses Projekts.

Initialisieren Sie ein neues Poetry-Projekt:

```bash
poetry init --no-interaction
```

### Schritt 2: Installieren Sie das AI-Hub CLI

Das CLI-Tool automatisiert die meisten Einrichtungsaufgaben:

```bash
poetry add --group dev aihub-cli
```

### Schritt 3: Generieren Sie die Plattforminfrastruktur

Erstellen Sie den Entwicklungs-Infrastruktur-Stack:

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

Dies erstellt die Datei `.env.core` mit sinnvollen Standardeinstellungen. Sie sehen Platzhalterwerte für die
OAuth2-Konfiguration – wir werden vorerst den Entwicklungsmodus verwenden, sodass Sie diese für erste Tests unverändert
lassen können.

## Starten der Plattform: 5 Minuten

Starten Sie die komplette AI-Hub Plattform:

```bash
docker compose -f docker-compose-platform.dev.yml --env-file .env.core up -d
```

Warten Sie, bis alle Services gestartet sind (beobachten Sie die Logs mit `docker compose logs -f`, wenn Sie den
Startvorgang sehen möchten).

**Überprüfen Sie, ob die Plattform läuft:**

- Öffnen Sie `http://localhost:8080` - Sie sollten die AI-Hub Weboberfläche sehen
- Sie werden feststellen, dass noch keine Agenten verfügbar sind – das ist normal!

::: warning Häufiges Startproblem
Sollten Services nicht starten, überprüfen Sie, ob die Ports 8080, 27017, 6379 und 4222 nicht bereits auf Ihrem System
verwendet werden.
:::

## Erstellen Sie Ihren ersten Agenten: 5 Minuten

### Schritt 1: Agenten-Grundgerüst generieren

Erstellen Sie Ihren ersten benutzerdefinierten Agenten:

```bash
poetry run aihub new-agent my_custom_agent
```

Dies erstellt eine vollständige Agentenstruktur:

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

Betrachten Sie den generierten Agentencode in `agents/my_custom_agent/MyCustomAgent/MyCustomAgent.py`:

```python
# TODO: tbd
```

Dieser Agent demonstriert die Kernmuster des SDK:

- **Ereignisgesteuerte Schritte** mit stark typisierten Ein- und Ausgaben
- **Automatische Plattformintegration** für Authentifizierung, Tracing und Monitoring
- **Einfache Geschäftslogik**, die Sie an Ihre Bedürfnisse anpassen können

### Schritt 3: Starten Sie Ihren Agenten

Generieren Sie eine Docker-Compose-Datei, die Ihren Agenten enthält:

```bash
poetry run aihub generate-agent-compose --with-agent my_custom_agent
```

Dies erstellt die Datei `docker-compose-agents.dev.yml` mit Ihrem Agenten, der für die Entwicklung konfiguriert ist (Hot
Reload inklusive).

Erstellen Sie eine einfache `.env`-Datei für die Agentenkonfiguration:

Starten Sie alles zusammen:

```bash
docker compose \
  -f docker-compose-platform.dev.yml \
  -f docker-compose-agents.dev.yml \
  --env-file .env.core \
  --env-file .env \
  up -d
```

## Überprüfen Sie Ihren Erfolg: 2 Minuten

### Schritt 1: Überprüfen Sie die Agentenregistrierung

Überprüfen Sie die Weboberfläche unter `http://localhost:8080`. Sie sollten nun Ihren Agenten `my_custom_agent` in den
Agentenlisten sehen, und er sollte als `online` angezeigt werden.

### Schritt 2: Testen Sie die Agenteninteraktion

Klicken Sie auf Ihren Agenten und senden Sie eine Testnachricht. Sie sollten eine Antwort erhalten, die zeigt, dass Ihr
Agent die Anfrage verarbeitet hat.

### Schritt 3: Beobachten Sie das Agentenverhalten

Besuchen Sie `http://localhost:6006`, um das Langfuse-Tracing zu sehen. Sie werden detaillierte Traces der Ausführung
Ihres Agenten sehen, die jeden Schritt sowie dessen Ein- und Ausgaben zeigen.

## Was ist gerade passiert?

In 15 Minuten haben Sie etwas Bemerkenswertes erreicht:

**Vollständige KI-Plattform:** Sie betreiben eine vollständige Enterprise-KI-Plattform mit Authentifizierung,
Monitoring, Kostenverfolgung und Observability.

**Integration benutzerdefinierter Agenten:** Ihr benutzerdefinierter Agent erbt automatisch alle Plattformfunktionen –
er erscheint in der Web-UI, verarbeitet Anfragen und verfolgt seine Ausführung ohne zusätzliche Konfiguration.

**Entwicklungsbereite Umgebung:** Das Hot-Reload-Setup bedeutet, dass Sie Ihren Agentencode ändern und Änderungen sofort
sehen können, ohne Container neu erstellen zu müssen.
