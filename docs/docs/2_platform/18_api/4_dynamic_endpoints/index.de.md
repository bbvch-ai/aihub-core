```markdown
---
title: Dynamische Agenten- und Prozess-Endpunkte
source_sha: "714f9ce43c8e9548622c524801384203ce305ccac59589e99df79aad2caa0153"
---

# Dynamische Agenten- und Prozess-Endpunkte :rocket: :100:

::: info **Kurz gesagt – Was sind dynamische Endpunkte?**
Der Swiss AI Hub erstellt automatisch REST API-Endpunkte on-the-fly, basierend auf den im System verfügbaren Agenten und Prozessen. Wenn ein neuer Agent oder Prozess online geht, generiert das API-Gateway sofort benutzerdefinierte Endpunkte, die auf die Fähigkeiten dieser spezifischen Komponente zugeschnitten sind. Dies eliminiert die Notwendigkeit einer manuellen API-Entwicklung und stellt sicher, dass Ihr System perfekt synchronisiert bleibt.
:::

## Was sind dynamische Endpunkte und wie funktionieren sie? :brain:

Dynamische Agenten- und Prozess-Endpunkte stellen einen revolutionären Ansatz zur API-Generierung in verteilten KI-Systemen dar. Anstatt statische API-Routen vorzudefinieren, setzt der Swiss AI Hub auf **intelligente Endpunkt-Discovery-Services**, die:

- **Kontinuierlich** den NATS Message Bus nach verfügbaren Agenten und Prozessen scannen
- **Automatisch** REST-Endpunkte basierend auf den Ereignisspezifikationen jeder Komponente generieren
- Diese Endpunkte zur Laufzeit **dynamisch** bei der FastAPI-Anwendung registrieren
- Die **Synchronisation** zwischen Ihren laufenden Services und den verfügbaren API-Endpunkten aufrechterhalten

Dieses System nutzt zwei zentrale Discovery Services:

- **`AgentEndpointsDiscoveryService`**: Erstellt Endpunkte wie `/agents/{agent_class}/{agent_id}/{event_name}` zum Senden von Ereignissen an bestimmte Agenten
- **`ProcessEndpointsDiscoveryService`**: Generiert Endpunkte wie `/processes/{process_class}/{process_id}/{route}` für die Interaktion von Menschen und Programmen mit Prozessen

Der Discovery-Prozess verwendet die **NATS-basierte Service Discovery**, um laufende Komponenten nach ihren Fähigkeiten abzufragen, und nutzt dann den **Jambo SchemaConverter**, um Ereignisschemata in Pydantic-Modelle umzuwandeln, die vollständig typisierte, dokumentierte API-Endpunkte antreiben.

## Warum dies Ihre KI-Strategie grundlegend verändert :trophy:

Diese Funktion beseitigt eine der größten Hürden für die Skalierung von KI-Systemen – die **API-Entwicklungsengpässe**:

**🔗 Zero-Configuration API-Generierung**: Neue Agenten und Prozesse legen ihre Fähigkeiten automatisch über REST APIs offen, ohne manuelle Entwicklung. Deployen Sie einen neuen Agenten, und seine Endpunkte erscheinen sofort in Ihrer API-Dokumentation.

**🧠 Typsichere dynamische Integration**: Jeder dynamische Endpunkt ist vollständig mit Pydantic-Modellen typisiert, die aus Ereignisschemata generiert werden, und bietet automatische Validierung, Serialisierung und umfassende OpenAPI-Dokumentation.

**🛡️ Enterprise-Grade Security**: Dynamische Endpunkte erben alle Sicherheitsfunktionen, einschließlich rollenbasierter Zugriffskontrolle, Authentifizierung und detaillierter Berechtigungen, wodurch neue Funktionen standardmäßig sicher sind.

**⚡ Echtzeit-Systemanpassung**: Ihre API passt sich automatisch an Systemänderungen an – wenn Agenten hoch- oder herunterskaliert werden, erscheinen oder verschwinden ihre Endpunkte entsprechend, wodurch Ihre Integrationsschicht perfekt synchronisiert bleibt.

**🌐 Nahtlose externe Integration**: Externe Systeme und Webhooks können über vorhersagbare REST-Endpunkte mit jedem Agenten oder Prozess interagieren, was leistungsstarke Integrationen mit Drittanbieter-Services und Geschäftssystemen ermöglicht.

::: details **Einrichtung und Nutzung dynamischer Endpunkte**
## Konfigurationsanforderungen

Dynamische Endpunkte werden automatisch aktiviert, wenn Sie den Swiss AI Hub mit dem vollständigen Infrastruktur-Stack starten:

1.  **NATS Message Bus**: Erforderlich für die Service-Discovery-Kommunikation
2.  **API Gateway**: Der `aihub_api`-Service mit aktiviertem `lifetime_manager`
3.  **Discovery Services**: Werden automatisch vom Lifetime Manager gestartet

## Generierung von Agenten-Endpunkten

Für jeden entdeckten Agenten erstellt das System Endpunkte nach diesem Muster:

```

POST /api/v1/agents/\{agent_class}/\{agent_id}/\{event_name}

```

**Beispiel**: Ein Agent mit der Klasse `rag_agent` und der ID `customer_support`, der `UserMessageEvent` akzeptiert, würde erhalten:

```

POST /api/v1/agents/rag_agent/customer_support/user_message_event

```

## Generierung von Prozess-Endpunkten

Für jeden entdeckten Prozess erstellt das System Endpunkte basierend auf der Prozessdefinition:

```

GET /api/v1/processes/\{process_class}/\{process_id}/\{route} # Formular abrufen POST
/api/v1/processes/\{process_class}/\{process_id}/\{route} # Formular absenden GET
/api/v1/processes/\{process_class}/\{process_id}/\{walkthrough_id}/\{route} # Prozess fortsetzen POST
/api/v1/processes/\{process_class}/\{process_id}/\{walkthrough_id}/\{route} # Fortsetzung absenden

```

## Verfügbare Funktionen

Dynamische Endpunkte bieten:

-   **Vollständige OpenAPI-Dokumentation**: Jeder Endpunkt erscheint in `/docs` mit vollständigen Anforderungs-/Antwortschemata
-   **Typ-Validierung**: Automatische Anforderungsvalidierung basierend auf Ereignisspezifikationen
-   **Authentifizierung**: Wird vom Basis-Controller-Sicherheitsmodell geerbt
-   **Fehlerbehandlung**: Standardisierte Fehlerantworten und HTTP-Statuscodes
-   **Caching**: Integriertes Response-Caching für Discovery-bezogene Operationen

## Sicherheit und Best Practices

**Zugriffskontrolle**:

-   Agenten-Endpunkte erfordern die Berechtigung `aihub.user.agent.{agent_class}.{agent_id}`
-   Prozess-Endpunkte erfordern die Berechtigung `aihub.user.process.{process_class}.{process_id}`

**Ratenbegrenzung**: Discovery Services laufen in konfigurierbaren Intervallen (Standard: 60 Sekunden), um die Reaktionsfähigkeit mit der Systemlast in Einklang zu bringen

**Monitoring**: Die Nutzung aller dynamischen Endpunkte wird über die Standard-Swiss AI Hub Observability Tools protokolliert und nachverfolgt

**Performance**: Dynamische Endpunkte werden zwischengespeichert und nur neu generiert, wenn sich die Systemtopologie ändert
:::

## Erste Schritte

Um dynamische Endpunkte in Ihrem Swiss AI Hub zu nutzen:

1.  **Infrastruktur starten**: Stellen Sie sicher, dass NATS und das API-Gateway mit dem Standard-Docker Compose Setup laufen
2.  **Agenten/Prozesse deployen**: Jeder Agent oder Prozess, der sich mit NATS verbindet, erhält automatisch Endpunkte
3.  **Endpunkte entdecken**: Überprüfen Sie `/api/v1/docs`, um alle dynamisch generierten Endpunkte zu sehen
4.  **Integrieren**: Nutzen Sie die Standard-REST-Endpunkte, um externe Systeme zu integrieren oder benutzerdefinierte Frontends zu erstellen

Das dynamische Endpunkt-System verwandelt den Swiss AI Hub von einer statischen API in eine lebendige, adaptive Integrationsschicht, die mit Ihren KI-Fähigkeiten wächst.
```
