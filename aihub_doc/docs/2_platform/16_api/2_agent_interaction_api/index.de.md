---
title: REST API zur Agenteninteraktion
source_sha: f91bbe9ed552290f61da3ec45bf79720de63a0ae450dde3311fdb51c48b8aa2e
---

# REST API zur Agenteninteraktion

## Konzept und Zweck

Die Agent Interaction REST API, basierend auf FastAPI, dient als plattform-native HTTP-Schnittstelle für den Zugriff auf
die vollen Funktionen des Swiss AI-Hub. Während die OpenAI-kompatible API einen standardisierten LLM-Zugriff für
Migrationsszenarien bietet, stellt diese API die vollständige Agenten-Orchestrierung, Prozessautomatisierung und
Plattformmanagement-Funktionalität bereit, die einzigartig für den Swiss AI-Hub ist.

Diese API wurde für Organisationen entwickelt, die native Anwendungen erstellen, welche die erweiterten Fähigkeiten der
Plattform nutzen: Multi-Agenten-Kollaboration, langlaufende Geschäftsprozesse, umfassende Beobachtbarkeit
(Observability) und anspruchsvolles Wissensmanagement. Sie bietet programmatische Kontrolle über den gesamten
Plattform-Lebenszyklus, von der Agenten-Erkennung und -Konfiguration über die Prozessausführung bis hin zur
Qualitätsbewertung.

## Wesentliche Designprinzipien

### Plattform-eigene Funktionen

Die API bietet direkten Zugriff auf Funktionen, die den Swiss AI-Hub von einfachen LLM-Proxys unterscheiden:
zustandsbehaftete Konversationen mit mehreren spezialisierten Agenten, orchestrierte Geschäftsprozesse, die KI mit
menschlichen Entscheidungspunkten koordinieren, umfassende Ereignisprotokolle für Audit und Debugging sowie
zentralisiertes Wissensmanagement für Retrieval-Augmented Generation (RAG). Diese Funktionen ermöglichen es
Organisationen, anspruchsvolle KI-gestützte Workflows anstelle einfacher Frage-Antwort-Interaktionen zu erstellen.

Anwendungen können verfügbare Agenten dynamisch entdecken, Multi-Agenten-Teams für spezifische Aufgaben konfigurieren,
komplexe Geschäftsprozesse initiieren und die Ausführung über detaillierte Ereignisströme überwachen. Diese Flexibilität
unterstützt sowohl interaktive Anwendungen, die sofortige Antworten erfordern, als auch Batch-Prozesse, die autonom über
längere Zeiträume laufen.

### Ereignisgesteuerte Integration

Die API dient als HTTP-Gateway zum ereignisgesteuerten Kern der Plattform und übersetzt synchrone HTTP-Anfragen in
asynchrone Plattform-Ereignisse. Diese Architektur bietet mehrere Vorteile: Anfragen kehren sofort zurück, während
Agenten Aufgaben im Hintergrund verarbeiten; verteilte Agentendienste skalieren unabhängig ohne API-Änderungen;
umfassende Ereignisströme ermöglichen Echtzeitüberwachung und historische Analyse; und Operationen bleiben über
strukturierte Ereignisprotokolle beobachtbar und debugfähig.

Dieses Design überbrückt traditionelle Request-Response-Erwartungen von Web- und mobilen Anwendungen mit dem
asynchronen, verteilten Charakter autonomer Agentenoperationen. Anwendungen erhalten sofortige Bestätigung ihrer
Anfragen, während die Plattform komplexe, potenziell langlaufende Agenten-Workflows orchestriert. .

## Geschäftswert

### Umfassende Plattformkontrolle

Im Gegensatz zu einfachen LLM-APIs, die grundlegenden Modellzugriff bieten, stellt diese Schnittstelle die gesamte
Plattform für Organisationen bereit, die anspruchsvolle KI-Lösungen entwickeln. Entwicklungsteams erhalten
programmatische Kontrolle über Agentenkonfiguration, Prozessorchestrierung und Wissensmanagement, ohne direkten
Infrastrukturzugriff zu benötigen. Dies ermöglicht Automatisierung auf Anwendungsebene unter Beibehaltung von
Sicherheitsgrenzen und Audit-Protokollen.

### Operative Transparenz und Compliance

Die umfassenden Beobachtbarkeitsfunktionen (Observability) erfüllen kritische Unternehmensanforderungen an Transparenz
und Compliance. Organisationen können Prüfern genau zeigen, wie KI-Systeme bestimmte Entscheidungen getroffen haben,
Konversationen zur Streitbeilegung rekonstruieren, Leistungsverschlechterungen erkennen, bevor sie Benutzer
beeinträchtigen, und Kosten überwachen, indem sie die Agentenausführung und Ressourcennutzung über Teams und Projekte
hinweg verfolgen.

### Skalierbare Multi-Agenten-Architekturen

Die Unterstützung der API für die Multi-Agenten-Kollaboration ermöglicht es Organisationen, skalierbare KI-Lösungen
durch die Komposition spezialisierter Agenten zu erstellen. Anstatt einzelne, monolithische Modelle für verschiedene
Aufgaben zu trainieren, können Organisationen fokussierte Agenten für spezifische Domänen entwickeln und diese über
diese Schnittstelle orchestrieren. Dieser modulare Ansatz reduziert die Komplexität einzelner Agenten, ermöglicht
unabhängige Agenten-Verbesserungszyklen und unterstützt die Wiederverwendung von Agenten in verschiedenen
Geschäftsprozessen.

## Implementierungsansatz

Basierend auf FastAPI, fungiert die API als Teil des Hauptplattformdienstes mit einem zustandslosen Design, das
horizontale Skalierung ermöglicht. Die Authentifizierung integriert sich über OAuth2 mit den Identitätsanbietern der
Organisation, und hierarchische Berechtigungen steuern den Ressourcenzugriff zur Laufzeit. Die Anfragenbearbeitung
übersetzt HTTP-Operationen in NATS-Ereignisse, die durch das Ereignissystem der Plattform fließen, wodurch eine saubere
Trennung zwischen der synchronen HTTP-Schnittstelle und der asynchronen Agentenausführung aufrechterhalten wird. Alle
Operationen werden über OpenTelemetry für verteiltes Tracing instrumentiert, und strukturiertes Logging erfasst
kontextbezogene Informationen für eine umfassende Beobachtbarkeit (Observability) über HTTP- und Ereignisgrenzen hinweg.
