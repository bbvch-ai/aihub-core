---
title: Proxy-Server
source_sha: 037993d1bb4c858e4249c90fa91c76df2a05d6752c21bd68faa8b80b8e66a4b2
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
  # Cloud model (Swiss LLM Cloud)
  - model_name: text-generation/gemma-4-31B-it
    litellm_params:
      model: openai/google/gemma-4-31B-it
      api_base: os.environ/SWISS_LLM_CLOUD_API_BASE_URL
      api_key: os.environ/SWISS_LLM_CLOUD_API_KEY
      drop_params: true
    model_info:
      mode: chat
      supports_function_calling: true
      input_cost_per_token: 0.0000002
      output_cost_per_token: 0.0000008

  # Local GPU model (vLLM)
  - model_name: text-generation/Qwen3-VL-30B-A3B-Instruct-FP8
    litellm_params:
      model: openai/qwen3-vl-30b
      api_base: http://vllm:8000/v1
      api_key: os.environ/LOCAL_LLM_TOKEN
      drop_params: true
    model_info:
      mode: chat
      supports_function_calling: true
      supports_vision: true
      input_cost_per_token: 0
      output_cost_per_token: 0
```

Der `model_name` identifiziert das Modell in Agent-Konfigurationen unter Verwendung des echten kanonischen Modellnamens.
Der Abschnitt `litellm_params` enthält anbieterspezifische Verbindungsdetails. Der Abschnitt `model_info` spezifiziert
Funktionen und Preisgestaltung pro Token für die Kostenverfolgung durch Langfuse.
:::

## Kernfunktionen

Vereinheitlichte Schnittstelle: LiteLLM bietet eine OpenAI-kompatible API, die mit der Swiss LLM Cloud, lokal gehosteten
vLLM-Modellen und anderen Anbietern funktioniert. Plattformcode verwendet dieselbe Schnittstelle, unabhängig davon,
welches Modell die Anfrage verarbeitet.

Anfrage-Routing: Der Proxy leitet Anfragen basierend auf der konfigurierten Strategie weiter. Die aktuelle Konfiguration
verwendet „usage-based-routing-v2“, welches die Last auf die verfügbaren Modelle verteilt.

Kostenverfolgung: Die Nutzungsverfolgung erfasst den Token-Verbrauch pro Anfrage. Die Kosten pro Token werden für jedes
Modell konfiguriert, wodurch die Plattform die Kosten pro Konversation berechnen und anzeigen kann. Weitere Details zur
Kostenverfolgung und -optimierung finden Sie unter [Kostenkontrolle](../../14_cost_control/).

PII-Schutz: Die Presidio-Integration (sofern aktiviert) scannt Anfragen nach persönlich identifizierbaren Informationen,
bevor diese an externe Anbieter gesendet werden. Weitere Details finden Sie unter
[Datenanonymisierung](../2_anonymization/).

Wiederholungsrichtlinien: Die Konfiguration spezifiziert die Anzahl der Wiederholungsversuche für Timeout-Fehler,
Ratenbegrenzungsfehler und interne Serverfehler.
