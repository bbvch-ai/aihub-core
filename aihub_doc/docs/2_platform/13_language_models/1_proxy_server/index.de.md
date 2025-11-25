---
title: Proxy-Server
source_sha: de3d79f6698370a529f2caad007d3b034c387de6b1abe5a2fd765d7af7210c8f
---

# LLM-Proxy

Der LLM-Proxy (LiteLLM) bietet ein zentralisiertes Gateway zu Sprachmodell-Anbietern. Er abstrahiert anbieterspezifische
APIs hinter einer OpenAI-kompatiblen Schnittstelle, wodurch die Plattform mit mehreren KI-Anbietern zusammenarbeiten
kann, ohne den Code ändern zu müssen.

## Konfiguration

Modelle werden in der LiteLLM-Konfigurationsdatei konfiguriert. Jeder Modelleintrag spezifiziert den Anbieter, den
API-Endpunkt, die Authentifizierung und die Fähigkeiten.

::: details Beispiel-Modellkonfiguration:
```yaml
model_list:
  - model_name: azure/gpt-4o-mini
    litellm_params:
      model: azure/gpt-4o-mini
      api_base: https://your-resource.openai.azure.com/
      api_key: os.environ/AZURE_OPENAI_KEY
      api_version: "2024-12-01-preview"
    model_info:
      mode: chat

  - model_name: google/gemini-2.5-flash
    litellm_params:
      model: gemini/gemini-2.5-flash
      api_key: os.environ/GEMINI_API_KEY
    model_info:
      mode: chat

  - model_name: local/qwen-2.5-multimodal-small
    litellm_params:
      model: openai/Qwen2.5-VL-3B-Instruct
      api_base: http://llama-cpp:8187/v1
      api_key: None
    model_info:
      mode: chat
      supports_function_calling: true
      supports_vision: true
```

Der `model_name` identifiziert das Modell in den Agentenkonfigurationen. Der Abschnitt `litellm_params` enthält
anbieterspezifische Verbindungsdetails. Der Abschnitt `model_info` spezifiziert Funktionen wie Chat, Embedding, Vision
oder Function Calling.
:::

## Kernfunktionen

Vereinheitlichte Schnittstelle: LiteLLM bietet eine OpenAI-kompatible API, die mit OpenAI, Google, Anthropic, Azure
OpenAI und selbst gehosteten Modellen funktioniert. Der Plattformcode verwendet dieselbe Schnittstelle, unabhängig
davon, welches Modell die Anfrage verarbeitet.

Anfrage-Routing: Der Proxy leitet Anfragen basierend auf der konfigurierten Strategie weiter. Die aktuelle Konfiguration
verwendet "usage-based-routing-v2", das die Last auf die verfügbaren Modelle verteilt.

Kostenverfolgung: Die Nutzungsverfolgung erfasst den Token-Verbrauch pro Anfrage. Die Kosten pro Token werden für jedes
Modell konfiguriert, wodurch die Plattform die Kosten pro Konversation berechnen und anzeigen kann. Weitere
Informationen zur Kostenverfolgung und -optimierung finden Sie unter [Kostenkontrolle](../../14_cost_control/).

PII-Schutz: Die Presidio-Integration (sofern aktiviert) scannt Anfragen nach persönlich identifizierbaren Informationen,
bevor sie an externe Anbieter gesendet werden. Weitere Informationen finden Sie unter
[Datenanonymisierung](../2_anonymization/).

Wiederholungsrichtlinien: Die Konfiguration spezifiziert die Anzahl der Wiederholungsversuche für Timeout-Fehler,
Ratenbegrenzungsfehler und interne Serverfehler.
