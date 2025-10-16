---
title: Dynamische Agenten- und Prozess-Endpunkte
index: 4
source_sha: "3c5f600631fe7b24bd68a6f1d05667a5f18723f65d1d289bebee7ddf6f1af2e2"
---

# Dynamische Agenten- und Prozess-Endpunkte :rocket: :100:

::: info **TL;DR – Was sind dynamische Endpunkte?**
Der AI-Hub erstellt automatisch und dynamisch REST-API-Endpunkte basierend auf den in Ihrem System verfügbaren Agenten und Prozessen. Wenn ein neuer Agent oder Prozess online geht, generiert das API-Gateway sofort maßgeschneiderte Endpunkte, die auf die Fähigkeiten dieser spezifischen Komponente zugeschnitten sind, wodurch die Notwendigkeit einer manuellen API-Entwicklung entfällt und sichergestellt wird, dass Ihr System perfekt synchronisiert bleibt.
:::

## Was sind dynamische Endpunkte und wie funktionieren sie? :brain:

Dynamische Agenten- und Prozess-Endpunkte stellen einen revolutionären Ansatz zur API-Generierung in verteilten KI-Systemen dar. Anstatt statische API-Routen vorzudefinieren, setzt der AI-Hub auf **intelligente Endpunkt-Discovery-Services**, die:

- **Kontinuierlich** den NATS-Message-Bus nach verfügbaren Agenten und Prozessen scannen
- **Automatisch** REST-Endpunkte basierend auf den Ereignisspezifikationen jeder Komponente generieren
- **Dynamisch** diese Endpunkte zur Laufzeit bei der FastAPI-Anwendung registrieren
- **Die Synchronisation** zwischen Ihren laufenden Services und den verfügbaren API-Endpunkten aufrechterhalten

Dieses System nutzt zwei zentrale Discovery-Services:

- **`AgentEndpointsDiscoveryService`**: Erstellt Endpunkte wie `/agents/{agent_class}/{agent_id}/{event_name}` zum Senden von Ereignissen an spezifische Agenten
- **`ProcessEndpointsDiscoveryService`**: Generiert Endpunkte wie `/processes/{process_class}/{process_id}/{route}` für die Interaktion von Menschen und Programmen mit Prozessen

Der Discovery-Prozess verwendet die **NATS-basierte Service-Discovery**, um laufende Komponenten nach ihren Fähigkeiten abzufragen, und nutzt dann den **Jambo SchemaConverter**, um Ereignisschemata in Pydantic-Modelle umzuwandeln, die vollständig typisierte, dokumentierte API-Endpunkte ermöglichen.

## Warum dies ein Wendepunkt für Ihre KI-Strategie ist :trophy:

Diese Funktion beseitigt eine der größten Hürden bei der Skalierung von KI-Systemen – **API-Entwicklungsengpässe**:

**🔗 API-Generierung ohne Konfiguration**: Neue Agenten und Prozesse stellen ihre Fähigkeiten automatisch über REST-APIs bereit, ohne manuelle Entwicklung. Setzen Sie einen neuen Agenten ein, und seine Endpunkte erscheinen sofort in Ihrer API-Dokumentation.

**🧠 Typsichere dynamische Integration**: Jeder dynamische Endpunkt ist mit Pydantic-Modellen, die aus Ereignisschemata generiert wurden, vollständig typisiert, was eine automatische Validierung, Serialisierung und umfassende OpenAPI-Dokumentation ermöglicht.

**🛡️ Sicherheit auf Unternehmensniveau**: Dynamische Endpunkte erben alle Sicherheitsfunktionen, einschließlich rollenbasierter Zugriffssteuerung, Authentifizierung und fein abgestufter Berechtigungen, wodurch neue Funktionen standardmäßig sicher sind.

**⚡ Echtzeit-Systemanpassung**: Ihre API passt sich automatisch an Systemänderungen an – wenn Agenten skaliert werden (hoch oder runter), erscheinen oder verschwinden ihre Endpunkte entsprechend, wodurch Ihre Integrationsebene perfekt synchronisiert bleibt.

**🌐 Nahtlose externe Integration**: Externe Systeme und Webhooks können über vorhersehbare REST-Endpunkte mit jedem Agenten oder Prozess interagieren, was leistungsstarke Integrationen mit Drittanbieter-Services und Geschäftssystemen ermöglicht.

::: details **Einrichtung und Nutzung dynamischer Endpunkte**
## Konfigurationsanforderungen

Dynamische Endpunkte werden automatisch aktiviert, wenn Sie den AI-Hub mit dem vollständigen Infrastruktur-Stack starten:

1.  **NATS Message Bus**: Erforderlich für die Service-Discovery-Kommunikation
2.  **API Gateway**: Der Dienst `aihub_api` mit aktiviertem `lifetime_manager`
3.  **Discovery Services**: Werden automatisch vom Lifetime-Manager gestartet

## Generierung von Agenten-Endpunkten

Für jeden entdeckten Agenten erstellt das System Endpunkte nach diesem Muster:

```
POST /api/v1/agents/{agent_class}/{agent_id}/{event_name}
```

**Beispiel**: Ein Agent mit der Klasse `rag_agent` und der ID `customer_support`, der `UserMessageEvent` akzeptiert, würde Folgendes erhalten:

```
POST /api/v1/agents/rag_agent/customer_support/user_message_event
```

## Generierung von Prozess-Endpunkten

Für jeden entdeckten Prozess erstellt das System Endpunkte basierend auf der Prozessdefinition:

```
GET  /api/v1/processes/{process_class}/{process_id}/{route}         # Get form
POST /api/v1/processes/{process_class}/{process_id}/{route}         # Submit form
GET  /api/v1/processes/{process_class}/{process_id}/{walkthrough_id}/{route}  # Continue process
POST /api/v1/processes/{process_class}/{process_id}/{walkthrough_id}/{route}  # Submit continuation
```

## Verfügbare Funktionen

Dynamische Endpunkte bieten:

-   **Vollständige OpenAPI-Dokumentation**: Jeder Endpunkt erscheint in `/docs` mit vollständigen Anfrage-/Antwort-Schemata
-   **Typvalidierung**: Automatische Anfragevalidierung basierend auf Ereignisspezifikationen
-   **Authentifizierung**: Wird vom Sicherheitsmodell des Basis-Controllers geerbt
-   **Fehlerbehandlung**: Standardisierte Fehlerantworten und HTTP-Statuscodes
-   **Caching**: Eingebautes Antwort-Caching für Discovery-bezogene Operationen

## Sicherheit und Best Practices

**Zugriffskontrolle**:

-   Agenten-Endpunkte erfordern die Berechtigung `aihub.user.agent.{agent_class}.{agent_id}`
-   Prozess-Endpunkte erfordern die Berechtigung `aihub.user.process.{process_class}.{process_id}`

**Ratenbegrenzung**: Discovery-Services laufen in konfigurierbaren Intervallen (Standard: 60 Sekunden), um die Reaktionsfähigkeit mit der Systemlast auszugleichen

**Überwachung**: Alle Nutzungen dynamischer Endpunkte werden über standardmäßige AI-Hub-Observability-Tools protokolliert und verfolgt

**Leistung**: Dynamische Endpunkte werden gecacht und nur neu generiert, wenn sich die Systemtopologie ändert
:::

## Erste Schritte

Um die dynamischen Endpunkte in Ihrem AI-Hub zu nutzen, gehen Sie wie folgt vor:

1.  **Infrastruktur starten**: Stellen Sie sicher, dass NATS und das API-Gateway mit dem Standard-Docker-Compose-Setup laufen
2.  **Agenten/Prozesse deployen**: Jeder Agent oder Prozess, der sich mit NATS verbindet, erhält automatisch Endpunkte
3.  **Endpunkte entdecken**: Überprüfen Sie `/api/v1/docs`, um alle dynamisch generierten Endpunkte zu sehen
4.  **Integrieren**: Nutzen Sie die Standard-REST-Endpunkte, um externe Systeme zu integrieren oder benutzerdefinierte Frontends zu erstellen

Das dynamische Endpunktsystem verwandelt den AI-Hub von einer statischen API in eine lebendige, adaptive Integrationsschicht, die mit Ihren KI-Fähigkeiten wächst.
