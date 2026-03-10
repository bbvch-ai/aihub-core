---
title: Entwicklungsumgebung einrichten
source_sha: bbbed737dfd6d33f30174f6500ff7e4590f257868fb6036ff99d57f0e4d06e1b
---

[@mhoegger](https://github.com/mhoegger)

# Entwicklungsumgebung einrichten: Ihre ersten 15 Minuten mit dem SDK

Der Einstieg in das Swiss AI Hub SDK ist bewusst einfach gehalten. Innerhalb von 15 Minuten verfügen Sie über eine
vollständige Entwicklungsumgebung, in der Ihr erster benutzerdefinierter Agent reale Anfragen verarbeitet.

## Voraussetzungsprüfung

Bevor wir beginnen, stellen Sie sicher, dass Sie diese Tools installiert haben:

**Wesentliche Tools:**

- **Python 3.13** – Das SDK erfordert Python 3.13 für alle Komponenten
- **uv** – Für Abhängigkeitsmanagement und virtuelle Umgebungen
- **Docker & Docker Compose** – Zum Ausführen der Plattforminfrastruktur
- **make** – Zum Ausführen gängiger Entwicklungsbefehle

**Optional, aber hilfreich:**

- **Node.js LTS + pnpm** – Nur für die Frontend-Anpassung erforderlich
- **Postman** – Für API-Tests und -Erkundung
- **MongoDB Compass** – Für die Datenbankinspektion während der Entwicklung

::: tip Schneller Installationscheck
Überprüfen Sie Ihr Setup mit diesen Befehlen:

```bash
python --version    # Should show 3.13.x
uv --version        # Any recent version
docker --version    # Any recent version
make --version      # Any version
```
:::

## Projekteinrichtung: 3 Minuten

### Schritt 1: Projektstruktur erstellen

Erstellen Sie ein neues Python-Projekt und öffnen Sie ein Terminal im Stammverzeichnis dieses Projekts.

Initialisieren Sie ein neues uv-Projekt:

```bash
uv init
```

### Schritt 2: Swiss AI Hub CLI installieren

Das CLI-Tool automatisiert die meisten Einrichtungstasks:

```bash
uv add --dev swiss-ai-hub-cli
```

### Schritt 3: Plattforminfrastruktur generieren

Erstellen Sie den Entwicklungs-Infrastruktur-Stack:

```bash
uv run swiss-ai-hub generate-compose
```

Dies erstellt `docker-compose.platform.dev.yml` mit allen benötigten Services: NATS Messaging, MongoDB, Redis,
Vektordatenbanken und den Swiss AI Hub Plattformkomponenten.

### Schritt 4: Umgebung konfigurieren

Generieren Sie die Umgebungskonfiguration:

```bash
uv run swiss-ai-hub generate-env
```

Dies erstellt `.env.core` mit sinnvollen Standardeinstellungen. Sie sehen Platzhalterwerte für die OAuth2-Konfiguration
– wir verwenden vorerst den Entwicklungsmodus, sodass Sie diese für erste Tests unverändert lassen können.

## Plattform starten: 5 Minuten

Starten Sie die vollständige Swiss AI Hub Plattform:

```bash
docker compose -f docker-compose-platform.dev.yml --env-file .env.core up -d
```

Warten Sie, bis alle Services gestartet sind (beobachten Sie die Logs mit `docker compose logs -f`, wenn Sie den
Startvorgang sehen möchten).

**Überprüfen Sie, ob die Plattform läuft:**

- Öffnen Sie `http://localhost:8080` – Sie sollten die Swiss AI Hub Weboberfläche sehen.
- Sie werden feststellen, dass noch keine Agents verfügbar sind – das ist zu erwarten!

::: warning Häufiges Startproblem
Wenn Services nicht starten, überprüfen Sie, ob die Ports 8080, 27017, 6379 und 4222 nicht bereits auf Ihrem System
verwendet werden.
:::

## Erstellen Sie Ihren ersten Agent: 5 Minuten

### Schritt 1: Agent-Gerüst generieren

Erstellen Sie Ihren ersten benutzerdefinierten Agent:

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

### Schritt 2: Den generierten Agent untersuchen

Sehen Sie sich den generierten Agent-Code in `agents/my_custom_agent/MyCustomAgent/MyCustomAgent.py` an:

```python
# TODO: tbd
```

Dieser Agent demonstriert die Kernmuster des SDK:

- **Ereignisgesteuerte Schritte** mit stark typisierten Ein- und Ausgaben
- **Automatische Plattformintegration** für Authentifizierung, Tracing und Monitoring
- **Einfache Geschäftslogik**, die Sie an Ihre Bedürfnisse anpassen können

### Schritt 3: Ihren Agent starten

Generieren Sie eine Docker-Compose-Datei, die Ihren Agent enthält:

```bash
uv run swiss-ai-hub generate-agent-compose --with-agent my_custom_agent
```

Dies erstellt `docker-compose-agents.dev.yml` mit Ihrem Agent, der für die Entwicklung konfiguriert ist (inklusive Hot
Reload).

Erstellen Sie eine einfache `.env`-Datei für die Agent-Konfiguration:

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

Überprüfen Sie die Weboberfläche unter `http://localhost:8080`. Sie sollten nun Ihren Agent `my_custom_agent` in den
Agents gelistet sehen, der als `online` angezeigt wird.

### Schritt 2: Agent-Interaktion testen

Klicken Sie auf Ihren Agent und senden Sie eine Testnachricht. Sie sollten eine Antwort erhalten, die zeigt, dass Ihr
Agent die Anfrage verarbeitet hat.

### Schritt 3: Agent-Verhalten beobachten

Besuchen Sie `http://localhost:6006`, um Langfuse-Tracing zu sehen. Sie sehen detaillierte Traces der Ausführung Ihres
Agents, die jeden Schritt sowie dessen Ein- und Ausgaben zeigen.

## Was ist gerade passiert?

Innerhalb von 15 Minuten haben Sie etwas Bemerkenswertes erreicht:

**Vollständige KI-Plattform:** Sie betreiben eine vollständige Enterprise AI-Plattform mit Authentifizierung,
Monitoring, Kostenverfolgung und Observability.

**Benutzerdefinierte Agent-Integration:** Ihr benutzerdefinierter Agent erbt automatisch alle Plattformfähigkeiten – er
erscheint in der Web-UI, verarbeitet Anfragen und verfolgt seine Ausführung ohne zusätzliche Konfiguration.

**Entwicklungsbereite Umgebung:** Das Hot-Reload-Setup bedeutet, dass Sie Ihren Agent-Code ändern und Änderungen sofort
sehen können, ohne Container neu zu erstellen.
