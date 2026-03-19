---
title: Sprachmodelle
source_sha: 31da0279b545d5e5d1272c386a85eda7a5d6d5bd569fc1243cd1c57cf39494f5
---

# Sprachmodelle

Der Swiss AI Hub integriert sich über Sprachmodell-Anbieter mittels LiteLLM, einem einheitlichen Gateway, das Routing,
Kostenverfolgung und Sicherheit verwaltet. Agents greifen über diese Proxy-Schicht auf Modelle zu, ohne
anbieterspezifischen Code zu benötigen.

## Unterstützte Modelle

LiteLLM unterstützt über 100 LLM-Anbieter. Die Plattform kann sich mit jedem Anbieter integrieren, den LiteLLM
unterstützt.

Die Plattform verwendet ein Inferenzmodell im Dual-Modus:

- **Nicht-GPU-Deployments**: Swiss LLM Cloud (in der Schweiz gehosteter Anbieter) für Textgenerierung, Embedding,
  Re-Ranking, Transkription und OCR
- **GPU-Deployments**: Lokales vLLM auf einer NVIDIA RTX 6000 Pro (96 GB VRAM) für vollständig luftspaltgetrennten
  Betrieb
- Jeder zusätzliche OpenAI-kompatible API-Endpunkt kann über die LiteLLM-Konfiguration hinzugefügt werden

Modelle werden in LiteLLM mit Metadaten über Funktionen (Chat, Embedding, Vision, Funktionsaufrufe), Token-Limits und
Kosten konfiguriert. Agents geben in ihrer Konfiguration an, welches Modell verwendet werden soll. Das Hinzufügen neuer
Anbieter erfordert die Aktualisierung der LiteLLM-Konfigurationsdatei.

## Architektur

Die Plattform verwendet drei Schichten:

LLM-Proxy-Schicht: Bietet ein einheitliches Gateway zu Sprachmodell-Anbietern. Siehe [Proxy-Server](./1_proxy_server/)
für Routing, Kostenverfolgung und Wiederholungsversuche.

Agenten-Schicht: Agents implementieren Workflows mithilfe von LLMs über den Proxy. Siehe [Guards](./3_guards/) für
Eingabe- und Ausgabevalidierung.

Benutzer-Schicht: Benutzer interagieren mit Agents über Chat-Oberflächen.

## Wie die Schichten zusammenarbeiten

Wenn ein Benutzer eine Frage stellt:

1. Die Frage erreicht den Agent
2. Agenten-Eingabe-Guards (optional) validieren, ob die Frage angemessen ist
3. Presidio (falls aktiviert) scannt die Frage auf der Proxy-Schicht nach PII
4. Der Proxy leitet die Anfrage an den konfigurierten LLM-Anbieter weiter
5. Das LLM generiert eine Antwort
6. Agenten-Ausgabe-Guards (optional) überprüfen die Antwortqualität und redigieren PII aus abgerufenen Dokumenten
7. Die Antwort erreicht den Benutzer

Dieser geschichtete Ansatz bietet Defense-in-Depth sowohl für die Funktionalität (Guards gewährleisten Qualität) als
auch für die Sicherheit (Presidio schützt Benutzereingaben, Ausgabe-Guards schützen abgerufene Daten).

## Komponenten

- [Proxy-Server](./1_proxy_server/): LiteLLM-Konfiguration, Routing und Kostenverfolgung
- [Datenanonymisierung](./2_anonymization/): Presidio-Integration für PII-Schutz in Benutzereingaben
- [Guards](./3_guards/): Agenten-Ebene Eingabe- und Ausgabevalidierung für Qualität und Sicherheit
