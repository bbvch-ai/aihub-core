---
title: Plattform vs. SDK
index: 4
source_sha: "e328e94b2597b4513c7dd43645a70c3c6d3330d08417dea00326e2e91a973074"
---

# Plattform vs. SDK: Verständnis der dualen Architektur

Der Swiss AI Hub trennt bewusst die Plattform vom SDK. Diese Trennung ist keine architektonische Komplexität; es ist
ein strategisches Design, das Ihnen maximale Flexibilität bei der Einführung, Bereitstellung und Erweiterung des Systems bietet.

## Die Plattform: Ihre KI-Infrastruktur

Die Plattform umfasst alles, was beim Ausführen von `docker compose up` gestartet wird. Dazu gehören Datenbanken,
Message Queues, das LLM-Gateway, Vektorspeicher, das Authentifizierungssystem, Benutzeroberflächen und Überwachungstools.
Unter Apache 2.0-Lizenz können Sie sie nach Belieben bereitstellen, modifizieren und betreiben.

Betrachten Sie die Plattform als Ihr KI-Betriebssystem. Sie kümmert sich um:

- Wo Daten gespeichert und wie sie abgerufen werden
- Welche Modelle verfügbar sind und wie sie aufgerufen werden
- Wer worauf zugreifen kann und wie die Authentifizierung erfolgt
- Wie Komponenten kommunizieren und sich koordinieren
- Was Benutzer sehen und wie sie interagieren

Die Plattform funktioniert sofort. Stellen Sie sie bereit, und Sie haben ein funktionsfähiges KI-System mit
vorgefertigten Agents, Chat-Oberflächen und Integrationen. Sie können sie direkt nutzen, ohne eine einzige Zeile Code
schreiben zu müssen.

## Das SDK: Ihr Entwicklungsframework

Das SDK ist das Mittel, mit dem Sie neue Fähigkeiten entwickeln, die auf der Plattform ausgeführt werden. Es stellt
Basisklassen, Decorators, Muster und Tools bereit, die Ihre benutzerdefinierten Agents, Pipelines und Prozesse automatisch
mit der Plattforminfrastruktur kompatibel machen.

Wenn Sie mit dem SDK entwickeln, schreiben Sie Geschäftslogik, während das SDK die Plattformintegration übernimmt:

```python
class MyAgent(Agent):
    @step()
    async def analyze_document(self, event: DocumentEvent) -> AnalysisEvent:
        # Your business logic here
        return AnalysisEvent(results=analysis)
```

Dieser Agent übernimmt automatisch:

- Das Streamen von Updates über die WebSocket-Verbindungen der Plattform
- Das Erscheinen in der Chat-Oberfläche
- Die Verfolgung in Phoenix
- Die Berücksichtigung der Plattform-Authentifizierung
- Das Speichern des Zustands in Plattformdatenbanken
- Die Fehlerbehandlung gemäß Plattformmustern

## Warum die Trennung wichtig ist

**Bereitstellungsflexibilität**
Sie können die Plattform ohne jeglichen benutzerdefinierten Entwicklungscode bereitstellen. Teams können sofort mit
vorgefertigten Funktionen KI nutzen, während Entwickler an benutzerdefinierten Agents arbeiten. Die Plattform bietet
vom ersten Tag an einen Mehrwert.

**Entwicklungsunabhängigkeit**
Die SDK-Entwicklung erfolgt außerhalb der Plattform-Laufzeitumgebung. Entwickler arbeiten in ihrer IDE mit vertrauten Tools
und testen lokal vor der Bereitstellung. Es ist nicht notwendig, die interne Architektur der Plattform zu verstehen,
um Agents zu erstellen.

**Update-Isolation**
Plattform-Updates (neue Versionen von Phoenix, LiteLLM oder der Web-Benutzeroberfläche) beeinträchtigen Ihre
benutzerdefinierten Agents nicht. SDK-Updates (neue Decorators oder Muster) erfordern keine Plattformänderungen.
Jede Schicht entwickelt sich unabhängig voneinander.

**Klare Eigentumsgrenzen**
Die Plattform ist unter Apache 2.0 lizenziert, Sie besitzen Ihre Bereitstellung also vollständig. Das SDK hat eine
andere Lizenzierung (EUPL 1.2 für die Community-Version), wodurch klare Grenzen zwischen der Infrastruktur, die Sie
besitzen, und den Entwicklungstools, die Sie lizenzieren, geschaffen werden.

## Wie sie zusammenarbeiten

Die Magie geschieht durch klar definierte Schnittstellen:

**Ereignisverträge**
Das SDK definiert Ereignistypen, die die Plattform versteht. Wenn Ihr Agent ein `UserMessageEvent` aussendet, weiß
die Plattform, wie es weitergeleitet, gespeichert und angezeigt werden muss. Der Vertrag ist das Ereignisschema, nicht
die Implementierung.

**Discovery-Protokolle**
Mit dem SDK erstellte Agents melden sich über NATS-Nachrichten bei der Plattform an. Die Plattform entdeckt
verfügbare Agents dynamisch, ohne dass eine Konfiguration erforderlich ist.

**Ressourceninjektion**
Das SDK kennt Plattformressourcen (Datenbanken, LLM-Clients, Speicher). Wenn Ihr Agent diese benötigt, injiziert die
Plattform automatisch konfigurierte Instanzen.

**Standardisierte Muster**
Das SDK erzwingt Muster, die die Plattform erwartet. Workflow-Schritte, Kontextverwaltung und Fehlerbehandlung folgen
alle Konventionen, die die Plattform überwachen und verwalten kann.

## Ein praktischer Vergleich

Stellen Sie sich vor, Sie erstellen einen Dokumentenanalyse-Agenten:

**Ohne das SDK:**

- Benutzerdefinierte API-Endpunkte schreiben
- WebSocket-Streaming implementieren
- Authentifizierungsprüfungen hinzufügen
- Datenbankverbindungen konfigurieren
- Tracing manuell instrumentieren
- Eine Benutzeroberfläche erstellen
- Fehlerzustände behandeln
- Bereitstellung verwalten

**Mit dem SDK:**

```python
class DocumentAnalyzer(Agent):
    @step()
    async def analyze(self, doc: Document) -> Analysis:
        return analyze_document(doc)
```

Das SDK versteckt keine Komplexität, es eliminiert Redundanz. Die Plattform weiß bereits, wie man streamt,
authentifiziert, speichert, verfolgt, anzeigt und bereitstellt. Das SDK stellt die Muster bereit, um diese Funktionen zu nutzen.

## Lizenzierung und Geschäftsmodell

Die architektonische Trennung ermöglicht ein nachhaltiges Geschäftsmodell:

**Plattform (Apache 2.0)**: Nehmen Sie sie, stellen Sie sie bereit, modifizieren Sie sie, besitzen Sie sie. Keine Gebühren,
keine Einschränkungen. Dies beseitigt Einführungshürden und Bedenken hinsichtlich eines Vendor Lock-ins.

**SDK (Dual lizenziert)**:

- **Community Edition (EUPL 1.2)**: Kostenlos nutzbar, aber Modifikationen müssen zurückgegeben werden
- **Kommerzielle Edition**: Proprietäre Entwicklung ohne Sharing-Anforderungen

Dieses Modell bedeutet:

- Organisationen können die Plattform risikofrei einführen
- Grundlegende Anpassungen mit Plattformfunktionen bleiben kostenlos
- Fortgeschrittene SDK-Entwicklung trägt zur Community bei oder erfordert eine kommerzielle Lizenzierung
- Jeder profitiert von Plattformverbesserungen

## Wann Sie welches Teil benötigen

**Nur Plattform:** Sie möchten sicheren KI-Zugriff mit vorgefertigten Funktionen. Perfekt für Organisationen, die ihre
KI-Reise beginnen, oder Teams, die Standard-Agents benötigen.

**Plattform + SDK:** Sie benötigen benutzerdefinierte Agents, spezialisierte Pipelines oder komplexe
Prozessautomatisierung. Das SDK wird unerlässlich, wenn vorgefertigte Funktionen nicht ausreichen.

**SDK für die Migration:** Sie haben bestehende Agents, die mit anderen Frameworks erstellt wurden. Das SDK bietet
Migrationspfade, um diese plattform-nativ zu machen, während Ihre Investition in die Geschäftslogik erhalten bleibt.

Die Plattform betreibt Ihre KI-Infrastruktur. Das SDK schafft Ihren Wettbewerbsvorteil. Zusammen bieten sie ein
vollständiges Ökosystem, in dem die Infrastruktur gelöst und die Entwicklung optimiert wird, sodass Sie sich auf das
konzentrieren können, was Ihre KI-Anwendungen einzigartig macht.
