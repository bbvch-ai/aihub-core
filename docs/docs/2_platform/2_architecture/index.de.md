---
title: Plattform-Architektur
description: Technische Architektur der Swiss AI Hub Plattform — C4-Modell, Kommunikationsprotokoll, Netzwerkisolation, Laufzeitszenarien und Deployment-Topologie.
source_sha: 73397312d58291dc67c6cca3b806dd5af3c93664609169009ed82ff36a308f9d
---

# Plattform-Architektur

Dieser Abschnitt dokumentiert die technische Architektur des Swiss AI Hub. Der Inhalt hier ist ein Deep Dive — für eine
Marketing-Übersicht der Plattform, siehe [Kernkomponenten](../../1_vision_and_positioning/3_core_components/) und
[Infrastrukturschichten](../../1_vision_and_positioning/4_infrastructure_layers/) unter Vision & Positionierung.

Die Architektur wird mit [LikeC4](https://likec4.dev) modelliert und als interaktive Diagramme über Web-Komponenten
gerendert. Die Quelldateien befinden sich in `docs/likec4/` und werden vom Docs-Dev-Server automatisch neu generiert.
Nutzen Sie die C4-Hierarchie zur Navigation:

- **[Systemkontext](./1_system_context/)** — L1: Personen und externe Systeme, die mit Swiss AI Hub interagieren
- **[Container](./2_containers/)** — L2: Die First-Party-Pakete der Plattform, die Infrastruktur und deren Verbindungen;
  beinhaltet Tier-Aufschlüsselungen
- **[Swiss AI Agent-Protokoll](./3_swiss_ai_agent_protocol/)** — Steuerungs- / Anzeige-Ereignismodell über NATS
- **[Netzwerkisolation](./4_network_isolation/)** — Docker-Netzwerkzonen und Traffic-Policy

Demnächst, wenn das LikeC4-Modell erweitert wird:

- **Laufzeitszenarien** — dynamische Ansichten von Chat-Streaming, Dokumentenerfassung, Bot-in-the-Loop, Agent-Discovery
- **Deployment-Topologie** — Produktions-Deployment mit Agent-Instanzen pro Klasse, OIDC-Middleware, Host-Netzwerk
  OpenWebUI
- **Komponenten-Interna** — L3-Komponentenansichten für jedes First-Party-Paket (diese werden auf den jeweiligen
  Paketseiten unter [Code Deep Dive](../../6_code_deep_dive/) zu finden sein)
