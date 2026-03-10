---
title: Plattform vs. SDK
source_sha: c0e8612400634106a6e5bdce944bd10880edeb5ee995f9f8f31ee6ba4619f931
---

# Plattform vs. SDK: Das duale Architekturverständnis

Der Swiss AI Hub trennt bewusst die Plattform vom SDK. Diese Trennung ist keine architektonische Komplexität, sondern
ein strategisches Design, das Ihnen maximale Flexibilität bei der Adaption, dem Deployment und der Erweiterung des
Systems bietet.

## Die Plattform: Ihre KI-Infrastruktur

Die Plattform ist alles, was läuft, wenn Sie `docker compose up` ausführen. Sie umfasst die Datenbanken, Message Queues,
das LLM Gateway, Vector Stores, das Authentifizierungssystem, Benutzeroberflächen und Monitoring Tools. Apache
2.0-lizenziert, steht sie Ihnen zur Verfügung, um sie nach Belieben zu deployen, zu modifizieren und zu betreiben.

Stellen Sie sich die Plattform als Ihr KI-Betriebssystem vor. Sie übernimmt:

- Wo Daten gespeichert und wie darauf zugegriffen wird
- Welche Modelle verfügbar sind und wie sie aufgerufen werden
- Wer auf was zugreifen kann und wie die Authentifizierung erfolgt
- Wie Komponenten kommunizieren und sich koordinieren
- Was Benutzer sehen und wie sie interagieren

Die Plattform funktioniert sofort. Deployen Sie sie, und Sie haben ein funktionsfähiges KI-System mit vorgefertigten
Agents, Chat-Oberflächen und Integrationen. Sie können es unverändert nutzen, ohne eine Zeile Code zu schreiben.

## Das SDK: Ihr Entwicklungsframework

Das SDK ist der Weg, wie Sie neue Funktionen entwickeln, die auf der Plattform laufen. Es bietet Basiskonstrukte,
Decorators, Muster und Tools, die Ihre benutzerdefinierten Agents, Pipelines und Prozesse automatisch mit der
Plattform-Infrastruktur kompatibel machen.

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
- Wird in Langfuse getraced
- Respektiert die Plattform-Authentifizierung
- Speichert den Zustand in Plattform-Datenbanken
- Behandelt Fehler gemäß den Plattform-Mustern

## Warum die Trennung wichtig ist

**Deployment-Flexibilität** Sie können die Plattform ohne jeglichen benutzerdefinierten Entwicklungscode deployen. Teams
können sofort mit der Nutzung von KI beginnen, indem sie vorgefertigte Funktionen verwenden, während Entwickler an
benutzerdefinierten Agents arbeiten. Die Plattform bietet vom ersten Tag an einen Mehrwert.

**Entwicklungsunabhängigkeit** Die SDK-Entwicklung erfolgt außerhalb der Plattform-Laufzeit. Entwickler arbeiten in
ihrer IDE mit vertrauten Tools und testen lokal, bevor sie deployen. Es ist nicht nötig, die interne Architektur der
Plattform zu verstehen, um Agents zu erstellen.

**Update-Isolation** Plattform-Updates (neue Versionen von Langfuse, LiteLLM oder der Web-UI) brechen Ihre
benutzerdefinierten Agents nicht. SDK-Updates (neue Decorators oder Muster) erfordern keine Plattform-Änderungen. Jede
Schicht entwickelt sich unabhängig voneinander.

**Klare Eigentumsgrenzen** Die Plattform ist Apache 2.0-lizenziert, sodass Sie Ihr Deployment vollständig besitzen. Das
SDK hat eine unterschiedliche Lizenzierung (EUPL 1.2 für die Community Edition), was klare Grenzen zwischen der
Infrastruktur, die Sie besitzen, und den Entwicklungstools, die Sie lizenzieren, schafft.

## Wie sie zusammenarbeiten

Die Magie entsteht durch klar definierte Schnittstellen:

**Event-Verträge** Das SDK definiert Event-Typen, die die Plattform versteht. Wenn Ihr Agent ein `UserMessageEvent`
aussendet, weiß die Plattform, wie es geroutet, gespeichert und angezeigt werden soll. Der Vertrag ist das Event-Schema,
nicht die Implementierung.

**Discovery-Protokolle** Mit dem SDK erstellte Agents melden sich über NATS-Nachrichten bei der Plattform an. Die
Plattform entdeckt verfügbare Agents dynamisch, ohne dass eine Konfiguration erforderlich ist.

**Ressourcen-Injektion** Das SDK kennt die Plattform-Ressourcen (Datenbanken, LLM Clients, Storage). Wenn Ihr Agent
diese benötigt, injiziert die Plattform automatisch konfigurierte Instanzen.

**Standardisierte Muster** Das SDK setzt Muster durch, die die Plattform erwartet. Workflow-Schritte, Kontextverwaltung,
Fehlerbehandlung – alles folgt Konventionen, die die Plattform überwachen und verwalten kann.

## Ein praktischer Vergleich

Stellen Sie sich vor, Sie entwickeln einen Dokumentenanalyse-Agent:

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

Das SDK versteckt keine Komplexität, sondern eliminiert Redundanz. Die Plattform weiß bereits, wie man streamt,
authentifiziert, speichert, traced, anzeigt und deployed. Das SDK bietet die Muster, um diese Funktionen zu nutzen.

## Lizenzierung und Geschäftsmodell

Die architektonische Trennung ermöglicht ein nachhaltiges Geschäftsmodell:

**Plattform (Apache 2.0)**: Nehmen Sie es, deployen Sie es, modifizieren Sie es, besitzen Sie es. Keine Gebühren, keine
Einschränkungen. Dies beseitigt Adaptionsbarrieren und Vendor-Lock-in-Bedenken.

**SDK (Dual lizenziert)**:

- **Community Edition (EUPL 1.2)**: Kostenlos nutzbar, aber Modifikationen müssen zurückgeteilt werden
- **Kommerzielle Edition**: Proprietäre Entwicklung ohne Weitergabeanforderungen

Dieses Modell bedeutet:

- Organisationen können die Plattform risikofrei adaptieren
- Grundlegende Anpassungen mit Plattformfunktionen bleiben kostenlos
- Fortgeschrittene SDK-Entwicklung trägt zur Community bei oder erfordert eine kommerzielle Lizenzierung
- Jeder profitiert von Plattformverbesserungen

## Wann Sie jeden Teil benötigen

**Nur Plattform:** Sie wünschen sich sicheren KI-Zugriff mit vorgefertigten Funktionen. Perfekt für Organisationen, die
ihre KI-Reise beginnen, oder Teams, die Standard-Agents benötigen.

**Plattform + SDK:** Sie benötigen benutzerdefinierte Agents, spezialisierte Pipelines oder komplexe
Prozessautomatisierung. Das SDK wird unerlässlich, wenn vorgefertigte Funktionen nicht ausreichen.

**SDK für die Migration:** Sie haben bestehende Agents, die mit anderen Frameworks erstellt wurden. Das SDK bietet
Migrationspfade, um sie plattform-nativ zu machen und gleichzeitig Ihre Investition in die Geschäftslogik zu erhalten.

Die Plattform betreibt Ihre KI-Infrastruktur. Das SDK baut Ihren Wettbewerbsvorteil auf. Zusammen bieten sie ein
vollständiges Ökosystem, in dem die Infrastruktur gelöst und die Entwicklung optimiert ist, wodurch Sie sich auf das
konzentrieren können, was Ihre KI-Anwendungen einzigartig macht.
