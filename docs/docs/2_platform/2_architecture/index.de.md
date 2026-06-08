---
title: Plattform-Architektur
description: Technische Architektur der Swiss AI Hub-Plattform – C4-Modell, Kommunikationsprotokoll, Netzwerkisolation, Laufzeit-Szenarien und Deployment-Topologie.
source_sha: 5b75cf067d86d785627a444968c4e06d0d5564d4f5b0cc33e216efdf57836441
---

# Plattform-Architektur

Dieser Abschnitt dokumentiert die technische Architektur des Swiss AI Hubs. Der Inhalt hier ist eine Vertiefung – eine
marketingorientierte Plattformübersicht finden Sie unter Vision & Positionierung in
[Kernkomponenten](/de/docs/1_vision_and_positioning/3_core_components/) und
[Infrastruktur-Layern](/de/docs/1_vision_and_positioning/4_infrastructure_layers/).

Die Architektur ist mit [LikeC4](https://likec4.dev) modelliert und wird als interaktive Diagramme über Web-Komponenten
gerendert. Quelldateien befinden sich in `docs/likec4/` und werden automatisch vom Docs-Dev-Server neu generiert.
Verwenden Sie die C4-Hierarchie zur Navigation:

- **[Systemkontext](/de/docs/platform_architecture/1_system_context/)** — L1: Personen und externe Systeme, die mit
  Swiss AI Hub interagieren
- **[Container](/de/docs/platform_architecture/2_containers/)** — L2: Die eigenen Pakete der Plattform, Infrastruktur
  und deren Verbindung; beinhaltet Tier-Aufschlüsselungen
- **[Swiss AI Agent-Protokoll](/de/docs/platform_architecture/3_swiss_ai_agent_protocol/)** —
  Steuerungs-/Anzeige-Ereignismodell über NATS
- **[Netzwerkisolation](/de/docs/platform_architecture/4_network_isolation/)** — Docker-Netzwerkzonen und Traffic-Policy

Demnächst, wenn das LikeC4-Modell erweitert wird:

- **Laufzeit-Szenarien** — dynamische Ansichten von Chat-Streaming, Dokumentenaufnahme, Bot-in-the-Loop, Agent-Erkennung
- **Deployment-Topologie** — Produktions-Deployment mit Agent-Instanzen pro Klasse, OIDC-Middleware, Host-Netzwerk
  OpenWebUI
- **Komponenten-Interna** — L3-Komponentenansichten für jedes eigene Paket (diese werden auf den jeweiligen Paketseiten
  unter [Code Deep Dive](/de/docs/6_code_deep_dive/) zu finden sein)
