---
title: Proxy-Server
source_sha: f1021f95bcc58de1dc6793dbd5a73d613f50056e498a9a0c2f434ce4019d6297
---

# LLM-Proxy

Der LLM-Proxy (LiteLLM) bietet ein zentralisiertes Gateway zu Sprachmodell-Anbietern. Er abstrahiert anbieterspezifische
APIs hinter einer OpenAI-kompatiblen Schnittstelle, sodass die Plattform mit mehreren KI-Anbietern arbeiten kann, ohne
den Code ändern zu müssen.

## Konfiguration

Modelle werden in der LiteLLM-Konfigurationsdatei konfiguriert. Jeder Modelleintrag spezifiziert den Anbieter, den
API-Endpunkt, die Authentifizierung und die Fähigkeiten.

::: details Beispielmodellkonfiguration:
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
Fähigkeiten und Preise pro Token für die Kostenverfolgung über Langfuse.
:::

## Kernfunktionen

Vereinheitlichte Schnittstelle: LiteLLM bietet eine OpenAI-kompatible API, die mit Swiss LLM Cloud, lokal gehosteten
vLLM-Modellen und anderen Anbietern funktioniert. Der Plattformcode verwendet dieselbe Schnittstelle, unabhängig davon,
welches Modell die Anfrage verarbeitet.

Anfrage-Routing: Der Proxy leitet Anfragen basierend auf der konfigurierten Strategie weiter. Die aktuelle Konfiguration
verwendet „usage-based-routing-v2“, welche die Last auf die verfügbaren Modelle verteilt.

Kostenverfolgung: Die Nutzungsverfolgung erfasst den Token-Verbrauch pro Anfrage. Die Kosten pro Token sind für jedes
Modell konfiguriert, sodass die Plattform die Kosten pro Konversation berechnen und anzeigen kann. Weitere Informationen
zur Kostenverfolgung und -optimierung finden Sie unter [Kostenkontrolle](../../14_cost_control/).

PII-Schutz: Die Presidio-Integration (sofern aktiviert) scannt Anfragen nach persönlich identifizierbaren Informationen,
bevor sie an externe Anbieter gesendet werden. Details finden Sie unter [Datenanonymisierung](../2_anonymization/).

Wiederholungsrichtlinien: Die Konfiguration spezifiziert die Anzahl der Wiederholungsversuche für Timeout-Fehler,
Ratenbegrenzungsfehler und interne Serverfehler.
