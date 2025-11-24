---
title: Plattform vs. SDK
source_sha: 710dca6b508c771b33ea3e2dad85d36d4800789818becf0ef98332d182d81315
---

# Plattform vs. SDK: Das duale Architekturverständnis

Der Swiss AI Hub trennt die Plattform bewusst vom SDK. Diese Trennung ist keine architektonische Komplexität, sondern
strategisches Design, das Ihnen maximale Flexibilität bei der Einführung, Bereitstellung und Erweiterung des Systems
bietet.

## Die Plattform: Ihre KI-Infrastruktur

Die Plattform umfasst alles, was beim Ausführen von `docker compose up` läuft. Sie beinhaltet Datenbanken, Message
Queues, das LLM Gateway, Vektorspeicher, das Authentifizierungssystem, Benutzeroberflächen und Monitoring-Tools. Unter
Apache 2.0-Lizenz steht sie Ihnen zur freien Bereitstellung, Modifikation und zum Betrieb zur Verfügung, ganz nach Ihren
Bedürfnissen.

Betrachten Sie die Plattform als Ihr KI-Betriebssystem. Sie verwaltet:

- Wo Daten gespeichert und wie sie abgerufen werden
- Welche Modelle verfügbar sind und wie sie aufgerufen werden
- Wer auf was zugreifen kann und wie die Authentifizierung erfolgt
- Wie Komponenten kommunizieren und koordinieren
- Was Benutzer sehen und wie sie interagieren

Die Plattform ist sofort einsatzbereit. Nach der Bereitstellung verfügen Sie über ein funktionales KI-System mit
vorgefertigten Agents, Chat-Oberflächen und Integrationen. Sie können es ohne jeglichen Code direkt verwenden.

## Das SDK: Ihr Entwicklungsframework

Das SDK ist das Mittel, mit dem Sie neue Funktionen entwickeln, die auf der Plattform ausgeführt werden. Es stellt
Basisklassen, Decorators, Muster und Tools bereit, die Ihre benutzerdefinierten Agents, Pipelines und Prozesse
automatisch mit der Plattforminfrastruktur kompatibel machen.

Wenn Sie mit dem SDK entwickeln, schreiben Sie die Geschäftslogik, während das SDK die Plattformintegration übernimmt:

```python
class MyAgent(Agent):
    @step()
    async def analyze_document(self, event: DocumentEvent) -> AnalysisEvent:
        # Your business logic here
        return AnalysisEvent(results=analysis)
```

Dieser Agent führt automatisch folgende Schritte aus:

- Streamt Updates über die WebSocket-Verbindungen der Plattform
- Erscheint in der Chat-Oberfläche
- Wird in Phoenix nachverfolgt
- Berücksichtigt die Plattform-Authentifizierung
- Speichert den Zustand in Plattform-Datenbanken
- Behandelt Fehler gemäß den Plattform-Mustern

## Warum die Trennung wichtig ist

**Bereitstellungsflexibilität** Sie können die Plattform ohne jeglichen benutzerdefinierten Entwicklungscode
bereitstellen. Teams können sofort mit vorgefertigten KI-Funktionen arbeiten, während Entwickler an kundenspezifischen
Agents arbeiten. Die Plattform bietet vom ersten Tag an einen Mehrwert.

**Entwicklungsunabhängigkeit** Die SDK-Entwicklung erfolgt außerhalb der Plattform-Laufzeitumgebung. Entwickler arbeiten
in ihrer IDE mit vertrauten Tools und testen lokal vor der Bereitstellung. Es ist nicht notwendig, die interne
Architektur der Plattform zu verstehen, um Agents zu erstellen.

**Update-Isolation** Plattform-Updates (neue Versionen von Phoenix, LiteLLM oder der Web-Benutzeroberfläche)
beeinträchtigen Ihre benutzerdefinierten Agents nicht. SDK-Updates (neue Decorators oder Muster) erfordern keine
Plattformänderungen. Jede Schicht entwickelt sich unabhängig voneinander.

**Klare architektonische Grenzen** Die Trennung schafft klare Schnittstellen zwischen Infrastruktur und
Geschäftslogik. Plattform-Belange (Authentifizierung, Speicherung, Tracing) sind vollständig von der Agent-Logik
getrennt. Dies macht die Codebasis leichter verständlich, testbar und wartbar.

## Wie sie zusammenarbeiten

Die Magie geschieht durch klar definierte Schnittstellen:

**Ereignisverträge** Das SDK definiert Ereignistypen, die die Plattform versteht. Wenn Ihr Agent ein `UserMessageEvent`
aussendet, weiß die Plattform, wie es geroutet, gespeichert und angezeigt wird. Der Vertrag ist das Ereignisschema,
nicht die Implementierung.

**Erkennungsprotokolle** Mit dem SDK erstellte Agents melden sich über NATS-Nachrichten bei der Plattform an. Die
Plattform erkennt verfügbare Agents dynamisch, ohne dass eine Konfiguration erforderlich ist.

**Ressourceninjektion** Das SDK kennt Plattformressourcen (Datenbanken, LLM-Clients, Speicher). Wenn Ihr Agent diese
benötigt, injiziert die Plattform automatisch konfigurierte Instanzen.

**Standardisierte Muster** Das SDK erzwingt Muster, die die Plattform erwartet. Workflow-Schritte, Kontextverwaltung und
Fehlerbehandlung folgen alle Konventionen, die die Plattform überwachen und verwalten kann.

## Ein praktischer Vergleich

Betrachten Sie die Erstellung eines Dokumentenanalyse-Agents:

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

Das SDK verbirgt keine Komplexität, sondern eliminiert Redundanz. Die Plattform weiß bereits, wie man streamt,
authentifiziert, speichert, nachverfolgt, anzeigt und bereitstellt. Das SDK bietet die Muster, um diese Funktionen zu
nutzen.

## Open Source und Lizenzierung

Der gesamte Swiss AI Hub ist Open-Source unter der Apache 2.0-Lizenz - Plattform, SDK, Agents, Pipelines und alle
Komponenten. Diese permissive Lizenz bedeutet, dass Sie alles frei nutzen, modifizieren und verbreiten können, auch für
kommerzielle Zwecke, ohne jegliche Verpflichtung, Ihre Änderungen zurückzugeben. Sie besitzen Ihre Bereitstellung und
Ihren Code vollständig.

## Wann Sie welche Komponente benötigen

**Nur Plattform:** Sie möchten sicheren KI-Zugang mit vorgefertigten Funktionen. Perfekt für Organisationen, die ihre
KI-Reise beginnen, oder Teams, die Standard-Agents benötigen.

**Plattform + SDK:** Sie benötigen benutzerdefinierte Agents, spezialisierte Pipelines oder komplexe
Prozessautomatisierung. Das SDK wird unerlässlich, wenn vorgefertigte Funktionen nicht ausreichen.

**SDK für die Migration:** Sie haben bestehende Agents, die mit anderen Frameworks erstellt wurden. Das SDK bietet
Migrationspfade, um sie plattform-nativ zu machen und gleichzeitig Ihre Investitionen in die Geschäftslogik zu bewahren.

Die Plattform betreibt Ihre KI-Infrastruktur. Das SDK schafft Ihren Wettbewerbsvorteil. Gemeinsam bieten sie ein
vollständiges Ökosystem, in dem die Infrastruktur gelöst und die Entwicklung optimiert ist, sodass Sie sich auf das
konzentrieren können, was Ihre KI-Anwendungen einzigartig macht.
