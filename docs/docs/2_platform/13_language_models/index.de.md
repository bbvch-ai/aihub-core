---
title: Sprachmodelle
source_sha: e85c749b8f199a056e09296d9ff6ca0f6dde3cfcda34049936966e64b8717cd9
---

# Sprachmodelle

Der Swiss AI Hub integriert sich über LiteLLM, ein vereinheitlichtes Gateway, das Routing, Kostenverfolgung und
Sicherheit verwaltet, mit Sprachmodell-Anbietern. Agents greifen über diese Proxy-Schicht auf Modelle zu, ohne
anbieterspezifischen Code zu benötigen.

## Unterstützte Modelle

LiteLLM unterstützt über 100 LLM-Anbieter. Die Plattform kann mit jedem von LiteLLM unterstützten Anbieter integriert
werden.

Die Plattform verwendet ein Dual-Mode-Inferenzmodell:

- **Nicht-GPU-Deployments**: Swiss LLM Cloud (in der Schweiz gehosteter Anbieter) für Textgenerierung, Embedding,
  Reranking, Transkription und OCR
- **GPU-Deployments**: Lokales vLLM auf einer NVIDIA RTX 6000 Pro (96 GB VRAM) für vollständig luftspaltgetrennten
  Betrieb
- Jeder zusätzliche OpenAI-kompatible API-Endpunkt kann über die LiteLLM-Konfiguration hinzugefügt werden

Modelle werden in LiteLLM mit Metadaten über deren Fähigkeiten (Chat, Embedding, Vision, Function Calling), Token-Limits
und Kosten konfiguriert. Agents geben in ihrer Konfiguration an, welches Modell verwendet werden soll. Das Hinzufügen
neuer Anbieter erfordert die Aktualisierung der LiteLLM-Konfigurationsdatei.

## Architektur

Die Plattform verwendet drei Schichten:

LLM-Proxy-Schicht: Bietet ein vereinheitlichtes Gateway zu Sprachmodell-Anbietern. Siehe
[Proxy-Server](./1_proxy_server/) für Routing, Kostenverfolgung und Wiederholungsversuche.

Agent-Schicht: Agents implementieren Workflows mithilfe von LLMs über den Proxy. Siehe [Guards](./3_guards/) für
Eingabe- und Ausgabevalidierung.

Benutzer-Schicht: Benutzer interagieren mit Agents über Chat-Oberflächen.

## Wie die Schichten zusammenarbeiten

Wenn ein Benutzer eine Frage stellt:

1. Die Frage erreicht den Agenten
2. Agent-Input-Guards (optional) validieren, ob die Frage angemessen ist
3. Presidio (falls aktiviert) scannt nach PII in der Frage auf der Proxy-Schicht
4. Der Proxy leitet die Anfrage an den konfigurierten LLM-Anbieter weiter
5. Das LLM generiert eine Antwort
6. Agent-Output-Guards (optional) prüfen die Antwortqualität und redigieren PII aus abgerufenen Dokumenten
7. Die Antwort erreicht den Benutzer

Dieser geschichtete Ansatz bietet Defense-in-Depth sowohl für die Funktionalität (Guards gewährleisten Qualität) als
auch für die Sicherheit (Presidio schützt Benutzereingaben, Output-Guards schützen abgerufene Daten).

## Komponenten

- [Proxy-Server](./1_proxy_server/): LiteLLM-Konfiguration, Routing und Kostenverfolgung
- [Datenanonymisierung](./2_anonymization/): Presidio-Integration zum Schutz von PII in Benutzereingaben
- [Guards](./3_guards/): Validierung von Eingaben und Ausgaben auf Agent-Ebene für Qualität und Sicherheit
