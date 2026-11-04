---
title: Proxy-Server
source_sha: efac4ae443008a50a4bbe8609a50ec9a80b8275ddc454868e5f80689fde27580
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

### Namen, Zweck und Fähigkeiten

Die Modellauswahl in der Admin-UI liest drei weitere Schlüssel aus `model_info`:

- **`aihub_display_name`:** der Name, den eine Modellauswahl anzeigt, etwa `Gemma 4 31B`. Jedes Modell der
  mitgelieferten Konfiguration setzt ihn. Ein Modell ohne ihn wird mit seinem `model_name` ohne Präfix angezeigt
  (`gemma-4-31B-it`).
- **`aihub_general_purpose`:** `false` für ein Modell, das für eine einzige Aufgabe gebaut ist und das eine
  Modellauswahl deshalb nie anbietet. Nur das OCR-Modell `MinerU2.5-2509-1.2B` setzt ihn auf `false`: Es wird über die
  Chat-API bereitgestellt, sein `mode` bleibt also `chat`, aber es kann kein Gespräch führen. `GET /models/mode/{mode}`
  lässt solche Modelle weg, ausser der Aufruf setzt `include_special_purpose=true`, und ein Agenten- oder Prozessprofil
  oder eine Wissensdatenbank, die eines nennt, wird beim Speichern abgewiesen. Ein Modell ohne den Schlüssel gilt als
  Allzweckmodell.
- **`supports_reasoning`:** ob das Modell überhaupt eine Denkphase erzeugen kann, neben den bestehenden
  `supports_function_calling`, `supports_response_schema` und `supports_vision`. Eine Modellauswahl, die eine Fähigkeit
  verlangt, behandelt ein nicht gesetztes Flag als nicht unterstützt.

```yaml
  - model_name: text-generation/MinerU2.5-2509-1.2B
    model_info:
      aihub_display_name: MinerU 2.5 (OCR)
      aihub_hosting_location: swiss_cloud
      aihub_general_purpose: false
      mode: chat
      supports_function_calling: false
      supports_response_schema: false
      supports_vision: true
      supports_reasoning: false
```

Der Konfigurationsgenerator weist ein Modell mit `mode: chat` ab, das nicht alle vier `supports_*`-Flags und
`aihub_general_purpose` auf `true` oder `false` setzt. Ein über die LiteLLM-UI hinzugefügtes Modell umgeht diese
Prüfung: Es bleibt auswählbar, fehlt aber in jeder Modellauswahl, die eine Fähigkeit verlangt, die es nicht deklariert.

LiteLLM gibt das `reasoning_effort` einer Anfrage an jedes Modell weiter, das es nicht kennt, unabhängig von
`supports_reasoning`. Lehnt ein Anbieter es ab, tragen Sie es in die `additional_drop_params` des Modells ein, wie es
die Konfiguration für Ministral tut.

### Embedding- und Reranking-Modelle

Die Plattform bemisst jede Eingabe an ein Embedding- oder Reranking-Modell, bevor sie sie sendet: Dokument-Chunks bei
der Ingestion, Suchanfragen und jedes Anfrage/Dokument-Paar eines Rerankings. Ein Modell weist eine Eingabe, die sein
Fenster überschreitet, mit einem Fehler ab, statt sie zu kürzen; die Zählung muss deshalb die des Modells selbst sein.
Jeder Eintrag mit `mode: embedding` oder `mode: rerank` deklariert daher neben `max_input_tokens` zwei Schlüssel:

- **`aihub_tokenizer`:** die ID eines Tokenizers, der in `packages/core` unter
  `swiss_ai_hub/core/generative_ai/resources/tokenizers/vendored/` mitgeliefert wird. Die Plattform zählt damit im
  Prozess, ohne Netzwerkaufruf. `bge-m3` deckt BAAI/bge-m3 und BAAI/bge-reranker-v2-m3 ab, die denselben Tokenizer
  verwenden.
- **`aihub_input_overhead_tokens`:** die Spezial-Tokens, die das Modell jeder Eingabe hinzufügt. bge-m3 fügt 2 hinzu
  (`<s> text </s>`), der bge-Reranker 4 pro Paar (`<s> query </s></s> document </s>`).

```yaml
  - model_name: embedding/bge-m3
    model_info:
      mode: embedding
      max_input_tokens: 8192
      aihub_tokenizer: bge-m3
      aihub_input_overhead_tokens: 2
```

Ein Modell ohne `aihub_tokenizer` funktioniert weiterhin: Seine Eingaben werden mit tiktoken gezählt und deutlich
innerhalb seines Fensters gehalten, wie vor der Einführung dieser Schlüssel, und jeder Prozess protokolliert eine
Warnung mit dem Namen des Modells. Um ein neues Modell exakt zu zählen, legen Sie unter `vendored/` einen Ordner mit der
Tokenizer-Datei, ihrer `LICENSE` und einer `SOURCE.json` (Repository, Revision, Datei, sha256, Format) an und nennen Sie
die ID des Ordners in der Konfiguration. Ein Unit-Test prüft, dass jedes Embedding- und Reranking-Modell in den
generierten Konfigurationen einen mitgelieferten Tokenizer nennt.

Die Apps lesen diese Schlüssel einmal pro Prozess. Erstellen Sie nach einer Änderung zuerst den LiteLLM-Container neu
und starten Sie danach die Apps neu.

## Kernfunktionen

Vereinheitlichte Schnittstelle: LiteLLM bietet eine OpenAI-kompatible API, die mit Swiss LLM Cloud, lokal gehosteten
vLLM-Modellen und anderen Anbietern funktioniert. Der Plattformcode verwendet dieselbe Schnittstelle, unabhängig davon,
welches Modell die Anfrage verarbeitet.

Anfrage-Routing: Der Proxy leitet Anfragen basierend auf der konfigurierten Strategie weiter. Die aktuelle Konfiguration
verwendet „simple-shuffle“: Jede Modellgruppe hat genau ein Deployment, eine nutzungsbasierte Strategie würde also nur
jedem Aufruf einen Redis-Schreibzugriff hinzufügen.

Antwort-Caching: Nur Embeddings werden in Valkey zwischengespeichert, für 24 Stunden. Chat-Antworten werden nicht
zwischengespeichert, weil ihre Prompts ganze angehängte Dateien enthalten und sich fast nie wiederholen.

Kostenverfolgung: Die Nutzungsverfolgung erfasst den Token-Verbrauch pro Anfrage. Die Kosten pro Token sind für jedes
Modell konfiguriert, sodass die Plattform die Kosten pro Konversation berechnen und anzeigen kann. Weitere Informationen
zur Kostenverfolgung und -optimierung finden Sie unter [Kostenkontrolle](../../14_cost_control/).

PII-Schutz: Die Guardrail `pii-anonymisation` ersetzt personenbezogene Daten in jeder Chat-Anfrage an ein Modell, das
ausserhalb des Deployments gehostet wird, durch Platzhalter und stellt sie in der Antwort wieder her, gestreamt oder
nicht. Details finden Sie unter [Datenanonymisierung](../2_anonymization/).

Wiederholungsrichtlinien: Die Konfiguration spezifiziert die Anzahl der Wiederholungsversuche für Timeout-Fehler,
Ratenbegrenzungsfehler und interne Serverfehler.
