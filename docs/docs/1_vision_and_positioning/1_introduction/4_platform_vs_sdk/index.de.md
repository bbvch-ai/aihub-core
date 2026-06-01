---
title: Plattform vs. SDK
source_sha: 943f5374c466240f75db8a8ee40e699da4632a84c0ff714960109d759ff67a78
---

# Plattform vs. SDK: Die duale Architektur verstehen

Der Swiss AI Hub trennt bewusst die Plattform vom SDK. Diese Trennung ist keine architektonische Komplexität; es ist ein
strategisches Design, das Ihnen maximale Flexibilität bei der Einführung, dem Deployment und der Erweiterung des Systems
bietet.

## Die Plattform: Ihre KI-Infrastruktur

Die Plattform umfasst alles, was beim Ausführen von `docker compose up` läuft. Sie beinhaltet Datenbanken, Message
Queues, das LLM Gateway, Vector Stores, das Authentifizierungssystem, Benutzeroberflächen und Monitoring Tools. Als
Open-Source (Apache 2.0 für die Runtime, AGPL-3.0 für die UI und das Backup; siehe
[LICENSES.md](https://github.com/bbvch-ai/aihub-core/blob/main/LICENSES.md) für die Aufschlüsselung pro Paket) steht es
Ihnen frei, diese nach Bedarf zu deployen, zu modifizieren und zu betreiben.

Stellen Sie sich die Plattform als Ihr KI-Betriebssystem vor. Sie verwaltet:

- Wo Daten gespeichert und wie darauf zugegriffen wird
- Welche Modelle verfügbar sind und wie sie aufgerufen werden
- Wer worauf zugreifen kann und wie die Authentifizierung erfolgt
- Wie Komponenten kommunizieren und koordinieren
- Was Benutzer sehen und wie sie interagieren

Die Plattform funktioniert sofort. Deployen Sie sie und Sie verfügen über ein funktionsfähiges KI-System mit
vorgefertigten Agents, Chat-Oberflächen und Integrationen. Sie können es ohne jeglichen Code sofort nutzen.

## Das SDK: Ihr Entwicklungsframework

Das SDK ist die Art und Weise, wie Sie neue Funktionen erstellen, die auf der Plattform laufen. Es bietet Basisklassen,
Decorators, Patterns und Tools, die Ihre benutzerdefinierten Agents, Pipelines und Prozesse automatisch mit der
Plattforminfrastruktur kompatibel machen.

Wenn Sie mit dem SDK entwickeln, schreiben Sie Geschäftslogik, während das SDK die Plattformintegration übernimmt:

```python
class MyAgent(Agent):
    @step()
    async def analyze_document(self, event: DocumentEvent) -> AnalysisEvent:
        # Your business logic here
        return AnalysisEvent(results=analysis)
```

Dieser Agent:

- Streamt Updates über die WebSocket-Verbindungen der Plattform
- Erscheint in der Chat-Oberfläche
- Wird in Langfuse getraced
- Respektiert die Plattform-Authentifizierung
- Speichert den Zustand in den Plattform-Datenbanken
- Behandelt Fehler gemäss den Plattform-Patterns

## Warum die Trennung wichtig ist

**Deployment-Flexibilität**\
Sie können die Plattform ohne jeglichen benutzerdefinierten Entwicklungscode deployen. Teams können sofort mit
vorgefertigten KI-Funktionen arbeiten, während Entwickler an benutzerdefinierten Agents arbeiten. Die Plattform bietet
vom ersten Tag an einen Mehrwert.

**Entwicklungsunabhängigkeit**\
Die SDK-Entwicklung findet ausserhalb der Plattform-Runtime statt. Entwickler arbeiten in ihrer IDE mit vertrauten Tools
und testen lokal, bevor sie deployen. Es ist nicht notwendig, die interne Architektur der Plattform zu verstehen, um
Agents zu erstellen.

**Update-Isolation**\
Plattform-Updates (neue Versionen von Langfuse, LiteLLM oder der Web-UI) unterbrechen Ihre benutzerdefinierten Agents
nicht. SDK-Updates (neue Decorators oder Patterns) erfordern keine Plattform-Änderungen. Jede Schicht entwickelt sich
unabhängig.

**Klare architektonische Grenzen**\
Die Trennung schafft klare Schnittstellen zwischen Infrastruktur und Geschäftslogik. Plattform-Anliegen
(Authentifizierung, Speicherung, Tracing) sind vollständig von der Agent-Logik getrennt. Dies erleichtert das
Verständnis, das Testen und die Wartung der Codebasis.

## Wie sie zusammenarbeiten

Die Magie entsteht durch klar definierte Schnittstellen:

**Event-Kontrakte**\
Das SDK definiert Event-Typen, die die Plattform versteht. Wenn Ihr Agent ein `UserMessageEvent` aussendet, weiss die
Plattform, wie sie es routen, speichern und anzeigen muss. Der Kontrakt ist das Event-Schema, nicht die Implementierung.

**Discovery-Protokolle**\
Mit dem SDK erstellte Agents melden sich über NATS-Nachrichten bei der Plattform an. Die Plattform entdeckt verfügbare
Agents dynamisch, ohne Konfiguration.

**Ressourcen-Injektion**\
Das SDK kennt Plattform-Ressourcen (Datenbanken, LLM-Clients, Storage). Wenn Ihr Agent diese benötigt, injiziert die
Plattform automatisch konfigurierte Instanzen.

**Standardisierte Patterns**\
Das SDK erzwingt Patterns, die die Plattform erwartet. Workflow-Schritte, Kontextverwaltung und Fehlerbehandlung folgen
alle Konventionen, die die Plattform überwachen und verwalten kann.

## Ein praktischer Vergleich

Betrachten Sie den Aufbau eines Dokumentenanalyse-Agenten:

**Ohne das SDK:**

- Benutzerdefinierte API-Endpunkte schreiben
- WebSocket-Streaming implementieren
- Authentifizierungsprüfungen hinzufügen
- Datenbankverbindungen konfigurieren
- Tracing manuell instrumentieren
- Eine Benutzeroberfläche erstellen
- Fehlerzustände behandeln
- Deployment verwalten

**Mit dem SDK:**

```python
class DocumentAnalyzer(Agent):
    @step()
    async def analyze(self, doc: Document) -> Analysis:
        return analyze_document(doc)
```

Das SDK verbirgt keine Komplexität, es eliminiert Redundanz. Die Plattform weiss bereits, wie man streamt,
authentifiziert, speichert, traced, anzeigt und deployt. Das SDK bietet die Patterns, um diese Funktionen zu nutzen.

## Open Source und Lizenzierung

Der Swiss AI Hub verwendet ein gemischtes Open-Source-Modell: Die Plattform-Runtime, das SDK, Agents, Pipelines und
Prozesse sind unter **Apache 2.0** lizenziert (permissiv — kommerzielle Nutzung, Modifikation, Distribution, keine
Verpflichtung zur Rückgabe von Änderungen); die Web-UI und die Backup-Orchestrierung unter **AGPL-3.0**; die
Multi-Tenant-Management-Plane ist proprietär und erfordert eine kommerzielle Lizenz. Eine vollständige Aufschlüsselung
pro Paket finden Sie unter [LICENSES.md](https://github.com/bbvch-ai/aihub-core/blob/main/LICENSES.md). Die Komponenten,
die Sie typischerweise erweitern – Ihre eigenen Agents, Pipelines und Prozesse, die auf dem SDK basieren – fallen unter
Apache 2.0, sodass Ihr Code Ihnen gehört.

## Wann Sie welche Komponente benötigen

**Nur Plattform:** Sie wünschen sich sicheren KI-Zugriff mit vorgefertigten Funktionen. Perfekt für Organisationen, die
ihre KI-Reise beginnen, oder Teams, die Standard-Agents benötigen.

**Plattform + SDK:** Sie benötigen benutzerdefinierte Agents, spezialisierte Pipelines oder komplexe
Prozessautomatisierung. Das SDK wird unerlässlich, wenn vorgefertigte Funktionen nicht ausreichen.

**SDK für die Migration:** Sie haben bestehende Agents, die mit anderen Frameworks erstellt wurden. Das SDK bietet
Migrationspfade, um diese Plattform-nativ zu machen und gleichzeitig Ihre Investitionen in die Geschäftslogik zu
erhalten.

Die Plattform betreibt Ihre KI-Infrastruktur. Das SDK schafft Ihren Wettbewerbsvorteil. Gemeinsam bilden sie ein
vollständiges Ökosystem, in dem die Infrastruktur gelöst und die Entwicklung optimiert ist, sodass Sie sich auf das
konzentrieren können, was Ihre KI-Anwendungen einzigartig macht.
