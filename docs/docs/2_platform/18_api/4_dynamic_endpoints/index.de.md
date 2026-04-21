```markdown
---
title: Dynamische Agenten- und Prozess-Endpunkte
source_sha: "eeaf1d80524a992b866b1e69c0142aa9a4fe966fe6ef26ae00cd3efef4027ac8"
---

# Dynamische Agenten- und Prozess-Endpunkte :rocket: :100:

::: info **TL;DR – Was sind dynamische Endpunkte?**
Der Swiss AI Hub erstellt automatisch REST API-Endpunkte on-the-fly basierend auf den in Ihrem System verfügbaren Agents und Prozessen. Wenn ein neuer Agent oder Prozess online geht, generiert das API-Gateway sofort benutzerdefinierte Endpunkte, die auf die Fähigkeiten dieser spezifischen Komponente zugeschnitten sind. Dies eliminiert die Notwendigkeit einer manuellen API-Entwicklung und stellt sicher, dass Ihr System perfekt synchronisiert bleibt.
:::

## Was sind dynamische Endpunkte und wie funktionieren sie? :brain:

Dynamische Agenten- und Prozess-Endpunkte stellen einen revolutionären Ansatz zur API-Generierung in verteilten KI-Systemen dar. Anstatt statische API-Routen vorzudefinieren, verwendet der Swiss AI Hub **intelligente Endpunkt-Entdeckungsdienste**, die:

- **Kontinuierlich** den NATS Message Bus nach verfügbaren Agents und Prozessen scannen
- **Automatisch** REST Endpunkte basierend auf den Ereignisspezifikationen jeder Komponente generieren
- **Dynamisch** diese Endpunkte zur Laufzeit bei der FastAPI-Anwendung registrieren
- **Die Synchronisation** zwischen Ihren laufenden Services und verfügbaren API-Endpunkten aufrechterhalten

Dieses System nutzt zwei zentrale Entdeckungsdienste:

- **`AgentEndpointsDiscoveryService`**: Erstellt Endpunkte wie `/agents/{agent_class}/{agent_id}/{event_name}`, um Ereignisse an spezifische Agents zu senden
- **`ProcessEndpointsDiscoveryService`**: Generiert Endpunkte wie `/processes/{process_class}/{process_id}/{route}` für die Interaktion von Menschen und Programmen mit Prozessen

Der Entdeckungsprozess verwendet die **NATS-basierte Service Discovery**, um laufende Komponenten nach ihren Fähigkeiten abzufragen, und nutzt dann den **Jambo SchemaConverter**, um Ereignisschemas in Pydantic-Modelle zu transformieren, die voll typisierte, dokumentierte API-Endpunkte ermöglichen.

## Warum dies ein Game-Changer für Ihre KI-Strategie ist :trophy:

Diese Funktion beseitigt eines der größten Hindernisse beim Skalieren von KI-Systemen – **API-Entwicklungsengpässe**:

**🔗 Zero-Configuration API-Generierung**: Neue Agents und Prozesse legen ihre Fähigkeiten automatisch über REST APIs offen, ohne manuelle Entwicklung. Deployen Sie einen neuen Agent, und seine Endpunkte erscheinen sofort in Ihrer API-Dokumentation.

**🧠 Typensichere dynamische Integration**: Jeder dynamische Endpunkt ist mit Pydantic-Modellen, die aus Ereignisschemas generiert werden, vollständig typisiert und bietet automatische Validierung, Serialisierung und umfassende OpenAPI-Dokumentation.

**🛡️ Enterprise-Grade Security**: Dynamische Endpunkte erben alle Sicherheitsfunktionen, einschliesslich rollenbasierter Zugriffssteuerung, Authentifizierung und detaillierter Berechtigungen, wodurch neue Funktionen standardmässig sicher sind.

**⚡ Echtzeit-Systemanpassung**: Ihre API passt sich automatisch Systemänderungen an – wenn Agents hoch- oder herunterskaliert werden, erscheinen oder verschwinden ihre Endpunkte entsprechend, wodurch Ihre Integrationsschicht perfekt synchronisiert bleibt.

**🌐 Nahtlose externe Integration**: Externe Systeme und Webhooks können über vorhersagbare REST-Endpunkte mit jedem Agent oder Prozess interagieren, was leistungsstarke Integrationen mit Drittanbieter-Services und Geschäftssystemen ermöglicht.

::: details **Einrichtung und Nutzung dynamischer Endpunkte**
## Konfigurationsanforderungen

Dynamische Endpunkte werden automatisch aktiviert, wenn Sie den Swiss AI Hub mit dem vollständigen Infrastruktur-Stack starten:

1.  **NATS Message Bus**: Erforderlich für die Service Discovery-Kommunikation
2.  **API Gateway**: Der `aihub_api`-Service mit aktiviertem `lifetime_manager`
3.  **Discovery Services**: Werden automatisch vom Lifetime Manager gestartet

## Agent-Endpunkt-Generierung

Für jeden entdeckten Agenten erstellt das System Endpunkte nach folgendem Muster:

```

POST /api/v1/\{tenant_id}/agents/\{agent_class}/\{agent_id}/\{event_name}

```

**Beispiel**: Ein Agent mit der Klasse `rag_agent` und der ID `customer_support`, der `UserMessageEvent` akzeptiert, würde folgendes erhalten:

```

POST /api/v1/\{tenant_id}/agents/rag_agent/customer_support/user_message_event

```

## Prozess-Endpunkt-Generierung

Für jeden entdeckten Prozess erstellt das System Endpunkte basierend auf der Prozessdefinition:

```

GET /api/v1/\{tenant_id}/processes/\{process_class}/\{process_id}/\{route} # Get form POST
/api/v1/\{tenant_id}/processes/\{process_class}/\{process_id}/\{route} # Submit form GET
/api/v1/\{tenant_id}/processes/\{process_class}/\{process_id}/\{walkthrough_id}/\{route} # Continue process POST
/api/v1/\{tenant_id}/processes/\{process_class}/\{process_id}/\{walkthrough_id}/\{route} # Submit continuation

```

## Verfügbare Funktionen

Dynamische Endpunkte bieten:

-   **Vollständige OpenAPI-Dokumentation**: Jeder Endpunkt erscheint in `/docs` mit vollständigen Request/Response-Schemata
-   **Typvalidierung**: Automatische Request-Validierung basierend auf Ereignisspezifikationen
-   **Authentifizierung**: Wird vom Sicherheitsmodell des Basis-Controllers geerbt
-   **Fehlerbehandlung**: Standardisierte Fehlerantworten und HTTP-Statuscodes
-   **Caching**: Integriertes Response-Caching für entdeckungsbezogene Operationen

## Sicherheit und Best Practices

**Zugriffskontrolle**:

-   Agent-Endpunkte erfordern die Berechtigung `aihub.user.agent.{agent_class}.{agent_id}`
-   Prozess-Endpunkte erfordern die Berechtigung `aihub.user.process.{process_class}.{process_id}`

**Ratenbegrenzung**: Discovery Services laufen in konfigurierbaren Intervallen (Standard: 60 Sekunden), um die Reaktionsfähigkeit mit der Systemlast auszugleichen

**Monitoring**: Die gesamte Nutzung dynamischer Endpunkte wird über die standardmässigen Swiss AI Hub Observability-Tools protokolliert und nachverfolgt

**Performance**: Dynamische Endpunkte werden gecacht und nur dann neu generiert, wenn sich die Systemtopologie ändert
:::

## Erste Schritte

Um dynamische Endpunkte in Ihrem Swiss AI Hub zu verwenden:

1.  **Starten Sie die Infrastruktur**: Stellen Sie sicher, dass NATS und das API-Gateway mit dem Standard Docker Compose Setup laufen
2.  **Deployen Sie Agents/Prozesse**: Jeder Agent oder Prozess, der sich mit NATS verbindet, erhält automatisch Endpunkte
3.  **Endpunkte entdecken**: Überprüfen Sie `/api/v1/active/docs`, um alle dynamisch generierten Endpunkte zu sehen
4.  **Integrieren**: Verwenden Sie die Standard-REST-Endpunkte, um externe Systeme zu integrieren oder benutzerdefinierte Frontends zu erstellen

Das dynamische Endpunktsystem verwandelt den Swiss AI Hub von einer statischen API in eine lebendige, adaptive Integrationsschicht, die mit Ihren KI-Fähigkeiten wächst.
```
