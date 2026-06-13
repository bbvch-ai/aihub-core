---
title: Plattform vs. SDK
source_sha: 5ed28d4f5a6809011a397e76c87da825792708d186ab3badaebd7595cc19302e
---

# Plattform vs. SDK: Die duale Architektur verstehen

Der Swiss AI Hub trennt Plattform und SDK bewusst. Diese Trennung ist keine architektonische Komplexität; sie ist ein
strategisches Design, das Ihnen maximale Flexibilität bei der Einführung, dem Deployment und der Erweiterung des Systems
bietet.

## Die Plattform: Ihre KI-Infrastruktur

Die Plattform umfasst alles, was beim Ausführen von `docker compose up` gestartet wird. Dazu gehören Datenbanken,
Message Queues, das LLM-Gateway, Vector Stores, das Authentifizierungssystem, Benutzeroberflächen und Überwachungstools.
Als Open-Source (Apache 2.0 für die Runtime, AGPL-3.0-or-later für die UI und das Backup; siehe
[LICENSES.md](https://github.com/bbvch-ai/aihub-core/blob/main/LICENSES.md) für die Aufschlüsselung pro Paket) steht sie
Ihnen zur Verfügung, um sie nach Ihren Bedürfnissen zu deployen, zu modifizieren und zu betreiben.

Betrachten Sie die Plattform als Ihr KI-Betriebssystem. Sie regelt:

- Wo Daten gespeichert und wie darauf zugegriffen wird
- Welche Modelle verfügbar sind und wie sie aufgerufen werden
- Wer auf was zugreifen kann und wie die Authentifizierung erfolgt
- Wie Komponenten kommunizieren und sich koordinieren
- Was Benutzer sehen und wie sie interagieren

Die Plattform funktioniert sofort. Deployen Sie sie, und Sie haben ein funktionsfähiges KI-System mit vorgefertigten
Agents, Chat-Oberflächen und Integrationen. Sie können sie sofort verwenden, ohne eine einzige Zeile Code schreiben zu
müssen.

## Das SDK: Ihr Entwicklungsframework

Das SDK ist die Art und Weise, wie Sie neue Funktionen entwickeln, die auf der Plattform ausgeführt werden. Es bietet
Basisklassen, Decorators, Muster und Tools, die Ihre benutzerdefinierten Agents, Pipelines und Prozesse automatisch mit
der Plattform-Infrastruktur kompatibel machen.

Wenn Sie mit dem SDK entwickeln, schreiben Sie Geschäftslogik, während das SDK die Plattformintegration übernimmt:

```python
class MyAgent(Agent):
    @step()
    async def analyze_document(self, event: DocumentEvent) -> AnalysisEvent:
        # Your business logic here
        return AnalysisEvent(results=analysis)
```

Dieser Agent übernimmt automatisch:

- Streamt Updates über die WebSocket-Verbindungen der Plattform
- Erscheint in der Chat-Oberfläche
- Wird in Langfuse nachverfolgt
- Berücksichtigt die Plattform-Authentifizierung
- Speichert den Zustand in Plattform-Datenbanken
- Behandelt Fehler gemäß den Plattform-Mustern

## Warum die Trennung wichtig ist

**Deployment-Flexibilität**\
Sie können die Plattform ohne jeglichen benutzerdefinierten Entwicklungscode deployen. Teams können sofort mit
vorgefertigten KI-Funktionen arbeiten, während Entwickler an benutzerdefinierten Agents arbeiten. Die Plattform bietet
vom ersten Tag an einen Mehrwert.

**Entwicklungsunabhängigkeit**\
Die SDK-Entwicklung erfolgt außerhalb der Plattform-Runtime. Entwickler arbeiten in ihrer IDE mit vertrauten Tools und
testen lokal vor dem Deployment. Es ist nicht notwendig, die interne Architektur der Plattform zu verstehen, um Agents
zu erstellen.

**Update-Isolation**\
Plattform-Updates (neue Versionen von Langfuse, LiteLLM oder der Web-UI) unterbrechen Ihre benutzerdefinierten Agents
nicht. SDK-Updates (neue Decorators oder Muster) erfordern keine Plattformänderungen. Jede Schicht entwickelt sich
unabhängig voneinander.

**Klare architektonische Grenzen**\
Die Trennung schafft klare Schnittstellen zwischen Infrastruktur und Geschäftslogik. Plattform-Belange
(Authentifizierung, Speicherung, Tracing) sind vollständig von der Agent-Logik getrennt. Dies macht die Codebasis
einfacher zu verstehen, zu testen und zu warten.

## Wie sie zusammenarbeiten

Die Magie geschieht durch klar definierte Schnittstellen:

**Event-Verträge**\
Das SDK definiert Ereignistypen, die die Plattform versteht. Wenn Ihr Agent ein `UserMessageEvent` ausgibt, weiß die
Plattform, wie sie es routen, speichern und anzeigen muss. Der Vertrag ist das Ereignisschema, nicht die
Implementierung.

**Discovery-Protokolle**\
Mit dem SDK erstellte Agents melden sich der Plattform über NATS-Nachrichten an. Die Plattform entdeckt verfügbare
Agents dynamisch, ohne Konfiguration.

**Ressourceninjektion**\
Das SDK kennt Plattform-Ressourcen (Datenbanken, LLM-Clients, Speicher). Wenn Ihr Agent diese benötigt, injiziert die
Plattform automatisch konfigurierte Instanzen.

**Standardisierte Muster**\
Das SDK erzwingt Muster, die die Plattform erwartet. Workflow-Schritte, Kontextverwaltung, Fehlerbehandlung – all dies
folgt Konventionen, die die Plattform überwachen und verwalten kann.

## Ein praktischer Vergleich

Betrachten Sie die Entwicklung eines Dokumentenanalyse-Agenten:

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

Das SDK verbirgt keine Komplexität, es eliminiert Redundanz. Die Plattform weiß bereits, wie man streamt,
authentifiziert, speichert, traced, anzeigt und deployt. Das SDK stellt die Muster bereit, um diese Funktionen zu
nutzen.

## Open Source und Lizenzierung

Der Swiss AI Hub verwendet ein gemischtes Open-Source-Modell: Die Plattform-Runtime, das SDK, Agents, Pipelines und
Prozesse sind unter **Apache 2.0** lizenziert (permissiv – kommerzielle Nutzung, Modifikation, Verteilung, keine
Verpflichtung zur Rückgabe von Änderungen); die Web-UI, die Multi-Mandanten-Management-Plane und die
Backup-Orchestrierung unter **AGPL-3.0-or-later** (Netzwerk-Copyleft). Eine vollständige Aufschlüsselung pro Paket
finden Sie unter [LICENSES.md](https://github.com/bbvch-ai/aihub-core/blob/main/LICENSES.md). Die Komponenten, die Sie
typischerweise erweitern – Ihre eigenen Agents, Pipelines und Prozesse, die auf dem SDK basieren – fallen unter Apache
2.0, sodass Ihr Code Ihnen gehört.

## Wann Sie welchen Teil benötigen

**Nur Plattform:**\
Sie möchten sicheren KI-Zugriff mit vorgefertigten Funktionen. Perfekt für Organisationen, die ihre KI-Reise beginnen,
oder Teams, die Standard-Agents benötigen.

**Plattform + SDK:**\
Sie benötigen benutzerdefinierte Agents, spezialisierte Pipelines oder komplexe Prozessautomatisierung. Das SDK wird
unerlässlich, wenn vorgefertigte Funktionen nicht ausreichen.

**SDK für Migration:**\
Sie haben bestehende Agents, die mit anderen Frameworks erstellt wurden. Das SDK bietet Migrationspfade, um diese
plattform-nativ zu machen, während Ihre Investition in die Geschäftslogik erhalten bleibt.

Die Plattform betreibt Ihre KI-Infrastruktur. Das SDK schafft Ihren Wettbewerbsvorteil. Gemeinsam bieten sie ein
vollständiges Ökosystem, in dem die Infrastruktur gelöst und die Entwicklung optimiert wird, sodass Sie sich auf das
konzentrieren können, was Ihre KI-Anwendungen einzigartig macht.
