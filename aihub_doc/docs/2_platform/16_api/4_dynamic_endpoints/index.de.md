---
title: Dynamische Agenten- und Prozess-Endpunkte
source_sha: 7076975953fb61f1eae377f279cb574dc478241ba999dbfd01b2130574533ac4
---

# Dynamische Agenten- und Prozess-Endpunkte :rocket: :100:

::: info **TL;DR - Was sind dynamische Endpunkte?**
Der AI-Hub erstellt automatisch REST-API-Endpunkte on-the-fly basierend auf den Agenten und Prozessen, die in Ihrem
System verfügbar sind. Wenn ein neuer Agent oder Prozess online geht, generiert das API-Gateway sofort maßgeschneiderte
Endpunkte, die auf die Fähigkeiten dieser spezifischen Komponente zugeschnitten sind, wodurch die Notwendigkeit einer
manuellen API-Entwicklung entfällt und sichergestellt wird, dass Ihr System perfekt synchronisiert bleibt.
:::

## Was sind dynamische Endpunkte und wie funktionieren sie? :brain:

Dynamische Agenten- und Prozess-Endpunkte stellen einen revolutionären Ansatz zur API-Generierung in verteilten
KI-Systemen dar. Anstatt statische API-Routen vorab zu definieren, nutzt der AI-Hub **intelligente
Endpunkt-Discovery-Dienste**, die:

- **Kontinuierlich** den NATS-Message-Bus nach verfügbaren Agenten und Prozessen **scannen**
- **Automatisch** REST-Endpunkte basierend auf den Ereignisspezifikationen jeder Komponente **generieren**
- Diese Endpunkte zur Laufzeit **dynamisch** bei der FastAPI-Anwendung **registrieren**
- Die **Synchronisation** zwischen Ihren laufenden Diensten und verfügbaren API-Endpunkten **aufrechterhalten**

Dieses System nutzt zwei zentrale Discovery-Dienste:

- **`AgentEndpointsDiscoveryService`**: Erstellt Endpunkte wie `/agents/{agent_class}/{agent_id}/{event_name}` zum
  Senden von Ereignissen an spezifische Agenten
- **`ProcessEndpointsDiscoveryService`**: Generiert Endpunkte wie `/processes/{process_class}/{process_id}/{route}` für
  die menschliche und programmatische Interaktion mit Prozessen

Der Discovery-Prozess verwendet eine **NATS-basierte Dienstentdeckung**, um laufende Komponenten nach ihren Fähigkeiten
abzufragen, und nutzt dann den **Jambo SchemaConverter**, um Ereignisschemata in Pydantic-Modelle umzuwandeln, die
vollständig typisierte, dokumentierte API-Endpunkte antreiben.

## Warum dies ein Wendepunkt für Ihre KI-Strategie ist :trophy:

Diese Funktion beseitigt eine der größten Hürden beim Skalieren von KI-Systemen – **Engpässe bei der API-Entwicklung**:

**🔗 API-Generierung ohne Konfiguration**: Neue Agenten und Prozesse machen ihre Fähigkeiten automatisch über REST-APIs
ohne manuelle Entwicklung verfügbar. Stellen Sie einen neuen Agenten bereit, und seine Endpunkte erscheinen sofort in
Ihrer API-Dokumentation.

**🧠 Typensichere dynamische Integration**: Jeder dynamische Endpunkt ist mit Pydantic-Modellen, die aus Ereignisschemata
generiert werden, vollständig typisiert und bietet automatische Validierung, Serialisierung und eine umfassende
OpenAPI-Dokumentation.

**🛡️ Unternehmenssicherheit**: Dynamische Endpunkte erben alle Sicherheitsfunktionen, einschließlich rollenbasierter
Zugriffskontrolle, Authentifizierung und detaillierter Berechtigungen, wodurch neue Funktionen standardmäßig sicher
sind.

**⚡ Echtzeit-Systemanpassung**: Ihre API passt sich automatisch an Systemänderungen an – wenn Agenten hoch- oder
herunterskalieren, erscheinen oder verschwinden ihre Endpunkte entsprechend, wodurch Ihre Integrationsschicht perfekt
synchronisiert bleibt.

**🌐 Nahtlose externe Integration**: Externe Systeme und Webhooks können über vorhersagbare REST-Endpunkte mit jedem
Agenten oder Prozess interagieren, was leistungsstarke Integrationen mit Drittanbieterdiensten und Geschäftssystemen
ermöglicht.

::: details **Einrichten und Verwenden dynamischer Endpunkte**
## Konfigurationsanforderungen

Dynamische Endpunkte werden automatisch aktiviert, wenn Sie den AI-Hub mit dem vollständigen Infrastruktur-Stack
starten:

1. **NATS Message Bus**: Erforderlich für die Dienstentdeckungs-Kommunikation
2. **API Gateway**: Der `aihub_api`-Dienst mit aktiviertem `lifetime_manager`
3. **Discovery Services**: Automatisch vom Lifetime Manager gestartet

## Agenten-Endpunkt-Generierung

Für jeden entdeckten Agenten erstellt das System Endpunkte nach diesem Muster:

```
POST /api/v1/agents/{agent_class}/{agent_id}/{event_name}
```

**Beispiel**: Ein Agent mit der Klasse `rag_agent` und der ID `customer_support`, der `UserMessageEvent` akzeptiert,
würde erhalten:

```
POST /api/v1/agents/rag_agent/customer_support/user_message_event
```

## Prozess-Endpunkt-Generierung

Für jeden entdeckten Prozess erstellt das System Endpunkte basierend auf der Prozessdefinition:

```
GET  /api/v1/processes/{process_class}/{process_id}/{route}         # Get form
POST /api/v1/processes/{process_class}/{process_id}/{route}         # Submit form
GET  /api/v1/processes/{process_class}/{process_id}/{walkthrough_id}/{route}  # Continue process
POST /api/v1/processes/{process_class}/{process_id}/{walkthrough_id}/{route}  # Submit continuation
```

## Verfügbare Funktionen

Dynamische Endpunkte bieten:

- **Vollständige OpenAPI-Dokumentation**: Jeder Endpunkt erscheint in `/docs` mit vollständigen
  Anforderungs-/Antwort-Schemata
- **Typvalidierung**: Automatische Anforderungsvalidierung basierend auf Ereignisspezifikationen
- **Authentifizierung**: Vom Basissicherheitsmodell des Controllers geerbt
- **Fehlerbehandlung**: Standardisierte Fehlerantworten und HTTP-Statuscodes
- **Caching**: Integriertes Antwort-Caching für Discovery-bezogene Operationen

## Sicherheit und Best Practices

**Zugriffskontrolle**:

- Agenten-Endpunkte erfordern die Berechtigung `aihub.user.agent.{agent_class}.{agent_id}`
- Prozess-Endpunkte erfordern die Berechtigung `aihub.user.process.{process_class}.{process_id}`

**Ratenbegrenzung**: Discovery-Dienste laufen in konfigurierbaren Intervallen (Standard: 60 Sekunden), um die
Reaktionsfähigkeit mit der Systemlast in Einklang zu bringen

**Überwachung**: Die Nutzung aller dynamischen Endpunkte wird über die Standard-AI-Hub-Observability-Tools protokolliert
und verfolgt

**Performance**: Dynamische Endpunkte werden zwischengespeichert und nur neu generiert, wenn sich die Systemtopologie
ändert
:::

## Erste Schritte

Um dynamische Endpunkte in Ihrem AI-Hub zu nutzen:

1. **Infrastruktur starten**: Stellen Sie sicher, dass NATS und das API-Gateway mit dem Standard-Docker Compose Setup
   laufen
2. **Agenten/Prozesse bereitstellen**: Jeder Agent oder Prozess, der sich mit NATS verbindet, erhält automatisch
   Endpunkte
3. **Endpunkte entdecken**: Überprüfen Sie `/api/v1/docs`, um alle dynamisch generierten Endpunkte zu sehen
4. **Integrieren**: Verwenden Sie die Standard-REST-Endpunkte, um externe Systeme zu integrieren oder benutzerdefinierte
   Frontends zu erstellen

Das dynamische Endpunktsystem verwandelt den AI-Hub von einer statischen API in eine lebendige, adaptive
Integrationsschicht, die mit Ihren KI-Fähigkeiten wächst.
