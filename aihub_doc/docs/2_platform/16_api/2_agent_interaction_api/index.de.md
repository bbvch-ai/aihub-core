---
title: Agenteninteraktions-REST-API
source_sha: 74fa0085309e70ab3b4c16aa1d4b46355ba95bab64a09f2803881b6cfc6327fb
---

# Agenteninteraktions-REST-API

## Konzept und Zweck

Die Agenteninteraktions-REST-API, basierend auf FastAPI, dient als plattform-native HTTP-Schnittstelle für den Zugriff
auf die vollen Funktionen des Swiss AI-Hub. Während die OpenAI-kompatible API einen standardisierten LLM-Zugriff für
Migrationsszenarien bietet, stellt diese API die vollständige Agenten-Orchestrierung, Prozessautomatisierung und
Plattformmanagement-Funktionalität bereit, die einzigartig für den Swiss AI-Hub ist.

Diese API wurde für Organisationen entwickelt, die native Anwendungen erstellen, welche die erweiterten Funktionen der
Plattform nutzen: Multi-Agenten-Kollaboration, langlebige Geschäftsprozesse, umfassende Observability und
anspruchsvolles Wissensmanagement. Sie bietet programmatische Kontrolle über den gesamten Plattform-Lebenszyklus, von
der Agentenentdeckung und -konfiguration über die Prozessausführung bis hin zur Qualitätsbewertung.

## Grundlegende Designprinzipien

### Plattform-eigene Funktionen

Die API bietet direkten Zugriff auf Funktionen, die den Swiss AI-Hub von einfachen LLM-Proxys unterscheiden:
zustandsbehaftete Konversationen mit mehreren spezialisierten Agenten, orchestrierte Geschäftsprozesse, die KI mit
menschlichen Entscheidungspunkten koordinieren, eine umfassende Ereignishistorie für Audit und Debugging sowie
zentralisiertes Wissensmanagement für die Retrieval-Augmented Generation. Diese Funktionen ermöglichen es
Organisationen, anspruchsvolle KI-gestützte Workflows anstatt einfacher Frage-Antwort-Interaktionen zu erstellen.

Anwendungen können verfügbare Agenten dynamisch entdecken, Multi-Agenten-Teams für spezifische Aufgaben konfigurieren,
komplexe Geschäftsprozesse initiieren und die Ausführung über detaillierte Ereignisströme überwachen. Diese Flexibilität
unterstützt sowohl interaktive Anwendungen, die sofortige Antworten benötigen, als auch Batch-Prozesse, die über längere
Zeiträume autonom ablaufen.

### Ereignisgesteuerte Integration

Die API dient als HTTP-Gateway zum ereignisgesteuerten Kern der Plattform und übersetzt synchrone HTTP-Anfragen in
asynchrone Plattformereignisse. Diese Architektur bietet mehrere Vorteile: Anfragen kehren sofort zurück, während
Agenten Aufgaben im Hintergrund verarbeiten; verteilte Agentendienste skalieren unabhängig ohne API-Änderungen;
umfassende Ereignisströme ermöglichen Echtzeitüberwachung und historische Analyse; und Operationen bleiben durch
strukturierte Ereignisprotokolle beobachtbar und debuggbar.

Dieses Design überbrückt traditionelle Anfrage-Antwort-Erwartungen von Web- und mobilen Anwendungen mit dem asynchronen,
verteilten Charakter autonomer Agentenoperationen. Anwendungen erhalten eine sofortige Bestätigung ihrer Anfragen,
während die Plattform komplexe, potenziell langlaufende Agenten-Workflows orchestriert.

## Geschäftlicher Nutzen

### Umfassende Plattformkontrolle

Im Gegensatz zu einfachen LLM-APIs, die grundlegenden Modellzugriff bieten, stellt diese Schnittstelle die volle
Plattform für Organisationen bereit, die anspruchsvolle KI-Lösungen entwickeln. Entwicklungsteams erhalten
programmatische Kontrolle über Agentenkonfiguration, Prozessorchestrierung und Wissensmanagement, ohne direkten
Infrastrukturzugriff zu benötigen. Dies ermöglicht Automatisierung auf Anwendungsebene unter Beibehaltung von
Sicherheitsgrenzen und Audit-Trails.

### Operationale Sichtbarkeit und Compliance

Die umfassenden Observability-Funktionen erfüllen kritische Unternehmensanforderungen an Transparenz und Compliance.
Organisationen können Prüfern genau zeigen, wie KI-Systeme bestimmte Entscheidungen getroffen haben, Konversationen zur
Streitbeilegung rekonstruieren, Leistungsabfälle identifizieren, bevor sie Benutzer beeinträchtigen, und Kosten
überwachen, indem sie die Agentenausführung und Ressourcennutzung über Teams und Projekte hinweg verfolgen.

### Skalierbare Multi-Agenten-Architekturen

Die Unterstützung der API für die Multi-Agenten-Kollaboration ermöglicht es Organisationen, skalierbare KI-Lösungen
durch die Komposition spezialisierter Agenten zu entwickeln. Anstatt einzelne, monolithische Modelle für vielfältige
Aufgaben zu trainieren, können Organisationen fokussierte Agenten für spezifische Domänen entwickeln und diese über
diese Schnittstelle orchestrieren. Dieser modulare Ansatz reduziert die Komplexität einzelner Agenten, ermöglicht
unabhängige Agentenverbesserungszyklen und unterstützt die Wiederverwendung von Agenten in verschiedenen
Geschäftsprozessen.

## Implementierungsansatz

Basierend auf FastAPI, arbeitet die API als Teil des Hauptplattformdienstes mit einem zustandslosen Design, das
horizontale Skalierung ermöglicht. Die Authentifizierung integriert sich über OAuth2 mit den Identitätsprovidern der
Organisation, und hierarchische Berechtigungen steuern den Ressourcenzugriff zur Laufzeit. Die Anfragenverarbeitung
übersetzt HTTP-Operationen in NATS-Ereignisse, die durch das Ereignissystem der Plattform fließen, wodurch eine saubere
Trennung zwischen der synchronen HTTP-Schnittstelle und der asynchronen Agentenausführung gewahrt bleibt. Alle
Operationen werden über OpenTelemetry für verteiltes Tracing instrumentiert, und strukturiertes Logging erfasst
kontextbezogene Informationen für eine umfassende Observability über HTTP- und Ereignisgrenzen hinweg.
