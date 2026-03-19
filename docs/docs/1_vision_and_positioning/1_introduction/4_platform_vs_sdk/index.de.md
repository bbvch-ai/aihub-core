---
title: Plattform vs. SDK
source_sha: b6725994e193c8d9c0a46bfc828dd8aabc6293cec36f1012608ed47d7cb9eeac
---

# Plattform vs. SDK: Das duale Architekturverständnis

Der Swiss AI Hub trennt die Plattform bewusst vom SDK. Diese Trennung ist keine architektonische Komplexität; sie ist
ein strategisches Design, das Ihnen maximale Flexibilität bei der Einführung, dem Deployment und der Erweiterung des
Systems bietet.

## Die Plattform: Ihre KI-Infrastruktur

Die Plattform ist alles, was ausgeführt wird, wenn Sie `docker compose up` ausführen. Sie umfasst die Datenbanken,
Message Queues, das LLM Gateway, Vector Stores, das Authentifizierungssystem, Benutzeroberflächen und Monitoring-Tools.
Unter der Apache 2.0 Lizenz steht sie Ihnen zur Verfügung, um sie nach Bedarf zu deployen, zu modifizieren und zu
betreiben.

Stellen Sie sich die Plattform als Ihr KI-Betriebssystem vor. Sie verwaltet:

- Wo Daten gespeichert und wie sie abgerufen werden
- Welche Modelle verfügbar sind und wie sie aufgerufen werden
- Wer auf was zugreifen kann und wie die Authentifizierung erfolgt
- Wie Komponenten kommunizieren und koordinieren
- Was Benutzer sehen und wie sie interagieren

Die Plattform funktioniert sofort. Deployen Sie sie und Sie haben ein funktionsfähiges KI-System mit vorgefertigten
Agents, Chat-Schnittstellen und Integrationen. Sie können sie unverändert nutzen, ohne eine einzige Codezeile zu
schreiben.

## Das SDK: Ihr Entwicklungsframework

Das SDK ist der Weg, wie Sie neue Fähigkeiten entwickeln, die auf der Plattform laufen. Es bietet Basisklassen,
Decorators, Muster und Tools, die Ihre benutzerdefinierten Agents, Pipelines und Prozesse automatisch mit der
Plattforminfrastruktur kompatibel machen.

Wenn Sie mit dem SDK entwickeln, schreiben Sie Geschäftslogik, während das SDK die Plattformintegration übernimmt:

```python
class MyAgent(Agent):
    @step()
    async def analyze_document(self, event: DocumentEvent) -> AnalysisEvent:
        # Your business logic here
        return AnalysisEvent(results=analysis)
```

Dieser Agent tut dies automatisch:

- Streamt Updates über die WebSocket-Verbindungen der Plattform
- Erscheint in der Chat-Oberfläche
- Wird in Langfuse getraced
- Respektiert die Plattform-Authentifizierung
- Speichert den Zustand in den Plattformdatenbanken
- Behandelt Fehler gemäss den Plattformmustern

## Warum die Trennung wichtig ist

**Deployment-Flexibilität** Sie können die Plattform ohne jeglichen benutzerdefinierten Entwicklungscode deployen. Teams
können sofort mit vorgefertigten KI-Fähigkeiten arbeiten, während Entwickler an benutzerdefinierten Agents arbeiten. Die
Plattform liefert vom ersten Tag an einen Mehrwert.

**Entwicklungsunabhängigkeit** Die SDK-Entwicklung erfolgt ausserhalb der Plattform-Laufzeit. Entwickler arbeiten in
ihrer IDE mit vertrauten Tools und testen lokal vor dem Deployment. Es ist nicht notwendig, die interne Architektur der
Plattform zu verstehen, um Agents zu erstellen.

**Update-Isolation** Plattform-Updates (neue Versionen von Langfuse, LiteLLM oder der Web-Benutzeroberfläche)
beeinträchtigen Ihre benutzerdefinierten Agents nicht. SDK-Updates (neue Decorators oder Muster) erfordern keine
Plattformänderungen. Jede Schicht entwickelt sich unabhängig voneinander.

**Klare Architektur-Grenzen** Die Trennung schafft klare Schnittstellen zwischen Infrastruktur und Geschäftslogik.
Plattform-Anliegen (Authentifizierung, Speicherung, Tracing) sind vollständig von der Agentenlogik getrennt. Dies macht
die Codebasis einfacher zu verstehen, zu testen und zu warten.

## Wie sie zusammenarbeiten

Die Magie entsteht durch wohldefinierte Schnittstellen:

**Event-Kontrakte** Das SDK definiert Event-Typen, die die Plattform versteht. Wenn Ihr Agent ein `UserMessageEvent`
emittiert, weiss die Plattform, wie sie es routen, speichern und anzeigen muss. Der Kontrakt ist das Event-Schema, nicht
die Implementierung.

**Discovery-Protokolle** Mit dem SDK erstellte Agents melden sich über NATS-Nachrichten bei der Plattform an. Die
Plattform entdeckt verfügbare Agents dynamisch, ohne dass eine Konfiguration erforderlich ist.

**Ressourcen-Injektion** Das SDK kennt Plattformressourcen (Datenbanken, LLM Clients, Speicher). Wenn Ihr Agent diese
benötigt, injiziert die Plattform automatisch konfigurierte Instanzen.

**Standardisierte Muster** Das SDK erzwingt Muster, die die Plattform erwartet. Workflow-Schritte, Kontextverwaltung und
Fehlerbehandlung folgen alle Konventionen, die die Plattform überwachen und verwalten kann.

## Ein praktischer Vergleich

Betrachten Sie den Aufbau eines Dokumentenanalyse-Agenten:

**Ohne das SDK:**

- Eigene API-Endpunkte schreiben
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
authentifiziert, speichert, tracet, anzeigt und deployt. Das SDK bietet die Muster, um diese Fähigkeiten zu nutzen.

## Open Source und Lizenzierung

Der gesamte Swiss AI Hub ist unter der Apache 2.0 Lizenz Open Source – Plattform, SDK, Agents, Pipelines und alle
Komponenten. Diese permissive Lizenz bedeutet, dass Sie alles frei nutzen, modifizieren und vertreiben können, auch für
kommerzielle Zwecke, ohne jegliche Verpflichtung, Ihre Modifikationen zurückzugeben. Sie besitzen Ihr Deployment und
Ihren Code vollständig.

## Wann Sie die einzelnen Teile benötigen

**Nur Plattform:** Sie möchten sicheren KI-Zugang mit vorgefertigten Fähigkeiten. Perfekt für Organisationen, die ihre
KI-Reise beginnen, oder Teams, die Standard-Agents benötigen.

**Plattform + SDK:** Sie benötigen benutzerdefinierte Agents, spezialisierte Pipelines oder komplexe
Prozessautomatisierung. Das SDK wird unerlässlich, wenn vorgefertigte Fähigkeiten nicht ausreichen.

**SDK für die Migration:** Sie haben bestehende Agents, die mit anderen Frameworks erstellt wurden. Das SDK bietet
Migrationspfade, um sie plattform-nativ zu machen und gleichzeitig Ihre Investition in die Geschäftslogik zu erhalten.

Die Plattform betreibt Ihre KI-Infrastruktur. Das SDK schafft Ihren Wettbewerbsvorteil. Gemeinsam bieten sie ein
vollständiges Ökosystem, in dem die Infrastruktur gelöst und die Entwicklung optimiert wird, sodass Sie sich auf das
konzentrieren können, was Ihre KI-Anwendungen einzigartig macht.
