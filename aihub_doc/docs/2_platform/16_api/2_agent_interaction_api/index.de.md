---
title: REST API für Agenten-Interaktion
index: 2
source_sha: "5feae53bae49726edf7b3296a2d969a31410af74c5883443cb28494cc6ee2dd4"
---

# REST API für Agenten-Interaktion

## Konzept und Zweck

Die REST API für Agenten-Interaktion, basierend auf FastAPI, dient als plattform-native HTTP-Schnittstelle für den Zugriff auf die vollen Funktionen des Swiss AI-Hub. Während die OpenAI-Kompatible API standardisierten LLM-Zugriff für Migrationsszenarien bietet, stellt diese API die vollständige Agenten-Orchestrierung, Prozessautomatisierung und Plattformmanagement-Funktionalität bereit, die einzigartig für den Swiss AI-Hub ist.

Diese API wurde für Organisationen entwickelt, die native Anwendungen erstellen, welche die erweiterten Fähigkeiten der Plattform nutzen: Multi-Agenten-Kollaboration, langlaufende Geschäftsprozesse, umfassende Beobachtbarkeit und ausgeklügeltes Wissensmanagement. Sie bietet programmatische Kontrolle über den gesamten Plattform-Lebenszyklus, von der Agenten-Entdeckung und -Konfiguration über die Prozessausführung bis hin zur Qualitätsbewertung.

## Kern-Designprinzipien

### Plattform-eigene Funktionen

Die API bietet direkten Zugriff auf Funktionen, die den Swiss AI-Hub von einfachen LLM-Proxys unterscheiden: zustandsbehaftete Konversationen mit mehreren spezialisierten Agenten, orchestrierte Geschäftsprozesse, die KI mit menschlichen Entscheidungspunkten koordinieren, eine umfassende Ereignishistorie für Audit und Debugging sowie ein zentralisiertes Wissensmanagement für die Retrieval-Augmented Generation. Diese Funktionen ermöglichen es Organisationen, anspruchsvolle KI-gestützte Workflows zu erstellen, anstatt einfacher Frage-Antwort-Interaktionen.

Anwendungen können verfügbare Agenten dynamisch entdecken, Multi-Agenten-Teams für spezifische Aufgaben konfigurieren, komplexe Geschäftsprozesse initiieren und die Ausführung über detaillierte Ereignisströme überwachen. Diese Flexibilität unterstützt sowohl interaktive Anwendungen, die sofortige Antworten erfordern, als auch Batch-Prozesse, die autonom über längere Zeiträume laufen.

### Ereignisgesteuerte Integration

Die API dient als HTTP-Gateway zum ereignisgesteuerten Kern der Plattform und übersetzt synchrone HTTP-Anfragen in asynchrone Plattformereignisse. Diese Architektur bietet mehrere Vorteile: Anfragen kehren sofort zurück, während Agenten Aufgaben im Hintergrund verarbeiten, verteilte Agenten-Services skalieren unabhängig ohne API-Änderungen, umfassende Ereignisströme ermöglichen Echtzeitüberwachung und historische Analyse, und Operationen bleiben durch strukturierte Ereignisprotokolle beobachtbar und debuggbar.

Dieses Design überbrückt traditionelle Anfrage-Antwort-Erwartungen von Web- und mobilen Anwendungen mit dem asynchronen, verteilten Charakter autonomer Agentenoperationen. Anwendungen erhalten eine sofortige Bestätigung der Anfragen, während die Plattform komplexe, potenziell langlaufende Agenten-Workflows orchestriert.

## Geschäftswert

### Umfassende Plattformkontrolle

Im Gegensatz zu einfachen LLM-APIs, die grundlegenden Modellzugriff bieten, stellt diese Schnittstelle die vollständige Plattform für Organisationen bereit, die anspruchsvolle KI-Lösungen entwickeln. Entwicklungsteams erhalten programmatische Kontrolle über Agentenkonfiguration, Prozessorchestrierung und Wissensmanagement, ohne direkten Infrastrukturzugriff zu benötigen. Dies ermöglicht Automatisierung auf Anwendungsebene unter Beibehaltung von Sicherheitsgrenzen und Audit-Protokollen.

### Operative Sichtbarkeit und Compliance

Die umfangreichen Beobachtbarkeitsfunktionen erfüllen kritische Unternehmensanforderungen an Transparenz und Compliance. Organisationen können Prüfern genau zeigen, wie KI-Systeme zu bestimmten Entscheidungen gelangten, Konversationen zur Streitbeilegung rekonstruieren, Leistungsverschlechterungen erkennen, bevor sie Benutzer beeinträchtigen, und Kosten überwachen, indem sie die Agentenausführung und Ressourcennutzung über Teams und Projekte hinweg verfolgen.

### Skalierbare Multi-Agenten-Architekturen

Die Unterstützung der API für die Multi-Agenten-Kollaboration ermöglicht es Organisationen, skalierbare KI-Lösungen durch die Komposition spezialisierter Agenten zu entwickeln. Anstatt einzelne, monolithische Modelle für verschiedene Aufgaben zu trainieren, können Organisationen fokussierte Agenten für spezifische Domänen entwickeln und diese über diese Schnittstelle orchestrieren. Dieser modulare Ansatz reduziert die Komplexität einzelner Agenten, ermöglicht unabhängige Agenten-Verbesserungszyklen und unterstützt die Wiederverwendung von Agenten in verschiedenen Geschäftsprozessen.

## Implementierungsansatz

Basierend auf FastAPI, arbeitet die API als Teil des Hauptplattformdienstes mit einem zustandslosen Design, das horizontale Skalierung ermöglicht. Die Authentifizierung integriert sich mit organisationsinternen Identitätsanbietern über OAuth2, und hierarchische Berechtigungen steuern den Ressourcenzugriff zur Laufzeit. Die Anfragenbearbeitung übersetzt HTTP-Operationen in NATS-Ereignisse, die durch das Ereignissystem der Plattform fließen, und sorgt so für eine saubere Trennung zwischen der synchronen HTTP-Schnittstelle und der asynchronen Agentenausführung. Alle Operationen werden über OpenTelemetry für verteiltes Tracing instrumentiert, und strukturiertes Logging erfasst kontextbezogene Informationen für eine umfassende Beobachtbarkeit über HTTP- und Ereignisgrenzen hinweg.
