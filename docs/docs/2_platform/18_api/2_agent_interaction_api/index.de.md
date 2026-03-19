---
title: REST API für die Agenteninteraktion
source_sha: "4a54f91f05f57aa865ab35e31fb05a6eef6ccb195335399785897ebf7207efcd"
---

# REST API für die Agenteninteraktion

## Konzept und Zweck

Die REST API für die Agenteninteraktion, die auf FastAPI basiert, dient als plattform-native HTTP-Schnittstelle für den Zugriff auf die vollen Funktionen des Swiss AI Hub. Während die OpenAI-kompatible API standardisierten LLM-Zugriff für Migrationsszenarien bietet, stellt diese API die vollständige Agenten-Orchestrierung, Prozessautomatisierung und Plattformmanagement-Funktionalität bereit, die für den Swiss AI Hub einzigartig ist.

Diese API wurde für Organisationen entwickelt, die native Anwendungen erstellen, welche die erweiterten Funktionen der Plattform nutzen: Multi-Agenten-Kollaboration, langlaufende Geschäftsprozesse, umfassende Observability und anspruchsvolles Wissensmanagement. Sie bietet programmatische Kontrolle über den gesamten Plattform-Lebenszyklus, von der Agenten-Entdeckung und -Konfiguration über die Prozessausführung bis hin zur Qualitätsbewertung.

## Grundlegende Designprinzipien

### Plattform-native Funktionen

Die API bietet direkten Zugriff auf Funktionen, die den Swiss AI Hub von einfachen LLM-Proxys unterscheiden: zustandsbehaftete Konversationen mit mehreren spezialisierten Agents, orchestrierte Geschäftsprozesse, die KI mit menschlichen Entscheidungspunkten koordinieren, umfassende Ereignishistorie für Audit und Debugging sowie zentralisiertes Wissensmanagement für Retrieval-Augmented Generation. Diese Funktionen ermöglichen es Organisationen, anspruchsvolle KI-gesteuerte Workflows statt einfacher Frage-Antwort-Interaktionen zu erstellen.

Anwendungen können verfügbare Agents dynamisch entdecken, Multi-Agenten-Teams für spezifische Aufgaben konfigurieren, komplexe Geschäftsprozesse initiieren und die Ausführung über detaillierte Ereignisströme überwachen. Diese Flexibilität unterstützt sowohl interaktive Anwendungen, die sofortige Antworten erfordern, als auch Batch-Prozesse, die über längere Zeiträume autonom laufen.

### Ereignisgesteuerte Integration

Die API dient als HTTP-Gateway zum ereignisgesteuerten Kern der Plattform und übersetzt synchrone HTTP-Anfragen in asynchrone Plattform-Ereignisse. Diese Architektur bietet mehrere Vorteile: Anfragen werden sofort zurückgegeben, während Agents Aufgaben im Hintergrund verarbeiten; verteilte Agenten-Services skalieren unabhängig ohne API-Änderungen; umfassende Ereignisströme ermöglichen Echtzeit-Monitoring und historische Analyse; und Operationen bleiben über strukturierte Ereignis-Logs beobachtbar und debuggbar.

Dieses Design überbrückt traditionelle Request-Response-Erwartungen von Web- und mobilen Anwendungen mit dem asynchronen, verteilten Charakter autonomer Agenten-Operationen. Anwendungen erhalten eine sofortige Bestätigung ihrer Anfragen, während die Plattform komplexe, potenziell langlaufende Agenten-Workflows orchestriert.

## Geschäftswert

### Umfassende Plattformkontrolle

Im Gegensatz zu einfachen LLM-APIs, die grundlegenden Modellzugriff bieten, stellt diese Schnittstelle die gesamte Plattform für Organisationen bereit, die anspruchsvolle KI-Lösungen entwickeln. Entwicklungsteams erhalten programmatische Kontrolle über Agenten-Konfiguration, Prozess-Orchestrierung und Wissensmanagement, ohne direkten Infrastrukturzugriff zu benötigen. Dies ermöglicht Automatisierung auf Anwendungsebene unter Beibehaltung von Sicherheitsgrenzen und Audit-Protokollen.

### Operative Transparenz und Compliance

Die umfassenden Observability-Funktionen erfüllen kritische Unternehmensanforderungen an Transparenz und Compliance. Organisationen können Auditoren genau aufzeigen, wie KI-Systeme zu bestimmten Entscheidungen gelangten, Konversationen zur Streitbeilegung rekonstruieren, Leistungsverschlechterungen identifizieren, bevor sie Benutzer beeinträchtigen, und Kosten überwachen, indem sie die Agenten-Ausführung und Ressourcennutzung über Teams und Projekte hinweg verfolgen.

### Skalierbare Multi-Agenten-Architekturen

Die Unterstützung der API für die Multi-Agenten-Kollaboration ermöglicht es Organisationen, skalierbare KI-Lösungen durch die Komposition spezialisierter Agents zu erstellen. Anstatt einzelne, monolithische Modelle für diverse Aufgaben zu trainieren, können Organisationen fokussierte Agents für spezifische Domänen entwickeln und diese über diese Schnittstelle orchestrieren. Dieser modulare Ansatz reduziert die Komplexität einzelner Agents, ermöglicht unabhängige Agenten-Verbesserungszyklen und unterstützt die Wiederverwendung von Agents in verschiedenen Geschäftsprozessen.

## Implementierungsansatz

Die API, basierend auf FastAPI, fungiert als Teil des Hauptplattformdienstes mit einem zustandslosen Design, das horizontale Skalierung ermöglicht. Die Authentifizierung integriert sich über OAuth2 mit den Identitätsanbietern der Organisation, und hierarchische Berechtigungen steuern den Ressourcenzugriff zur Laufzeit. Die Request-Verarbeitung übersetzt HTTP-Operationen in NATS-Ereignisse, die durch das Ereignissystem der Plattform fließen, und sorgt so für eine saubere Trennung zwischen der synchronen HTTP-Schnittstelle und der asynchronen Agenten-Ausführung. Alle Operationen werden über OpenTelemetry für verteiltes Tracing instrumentiert, und strukturiertes Logging erfasst kontextbezogene Informationen für eine umfassende Observability über HTTP- und Ereignisgrenzen hinweg.
