---
title: Sprachmodelle
source_sha: b8dc713984c2c19a94d83052ef10a249b2f3aac455e9309cca3c5b17829d258b
---

# Sprachmodelle

Der AI-Hub integriert Sprachmodell-Anbieter über LiteLLM, ein einheitliches Gateway, das Routing, Kostenverfolgung und
Sicherheit verwaltet. Agents greifen über diese Proxy-Schicht auf Modelle zu, ohne anbieterspezifischen Code zu
benötigen.

## Unterstützte Modelle

LiteLLM unterstützt über 100 LLM-Anbieter, darunter OpenAI, Azure OpenAI, Anthropic, Google, AWS Bedrock und andere. Die
Plattform kann mit jedem von LiteLLM unterstützten Anbieter integriert werden.

Derzeit konfigurierte Anbieter:

- Azure OpenAI-Modelle
- Google Gemini-Modelle
- Selbst gehostete Modelle über llama.cpp oder Hugging Face Text Embedding Inference
- Jeder OpenAI-kompatible API-Endpunkt

Modelle werden in LiteLLM mit Metadaten zu ihren Fähigkeiten (Chat, Embedding, Vision, Function Calling), Token-Limits
und Kosten konfiguriert. Agents geben in ihrer Konfiguration an, welches Modell verwendet werden soll. Das Hinzufügen
neuer Anbieter erfordert die Aktualisierung der LiteLLM-Konfigurationsdatei.

## Architektur

Die Plattform verwendet drei Schichten:

LLM-Proxy-Schicht: Bietet ein einheitliches Gateway zu Sprachmodell-Anbietern. Siehe [Proxy-Server](./1_proxy_server/)
für Routing, Kostenverfolgung und Wiederholungsversuche.

Agenten-Schicht: Agents implementieren Workflows unter Verwendung von LLMs über den Proxy. Siehe [Guards](./3_guards/)
für die Validierung von Eingaben und Ausgaben.

Benutzer-Schicht: Benutzer interagieren mit Agents über Chat-Oberflächen.

## Wie die Schichten zusammenarbeiten

Wenn ein Benutzer eine Frage stellt:

1. Die Frage erreicht den Agenten
2. Agenten-Eingangs-Guards (optional) validieren, ob die Frage angemessen ist
3. Presidio (falls aktiviert) scannt auf PII in der Frage auf der Proxy-Schicht
4. Der Proxy leitet die Anfrage an den konfigurierten LLM-Anbieter weiter
5. Das LLM generiert eine Antwort
6. Agenten-Ausgangs-Guards (optional) prüfen die Antwortqualität und redigieren PII aus abgerufenen Dokumenten
7. Die Antwort erreicht den Benutzer

Dieser geschichtete Ansatz bietet eine tiefgreifende Verteidigung sowohl für die Funktionalität (Guards sichern die
Qualität) als auch für die Sicherheit (Presidio schützt Benutzereingaben, Ausgangs-Guards schützen abgerufene Daten).

## Komponenten

- [Proxy-Server](./1_proxy_server/): LiteLLM-Konfiguration, Routing und Kostenverfolgung
- [Datenanonymisierung](./2_anonymization/): Presidio-Integration für PII-Schutz in Benutzereingaben
- [Guards](./3_guards/): Agenten-Ebenen-Validierung von Eingaben und Ausgaben für Qualität und Sicherheit
