---
title: Data anonymization
---

# Data anonymization

The Swiss AI Hub replaces personal data in requests to language models hosted outside your deployment with placeholders,
and puts the original values back into the answer before the user sees it. The external model never sees a name, an
address or an AHV number; the user reads a normal answer.

## What users see

A user asks: "Draft a reminder for Reto Wyss, AHV 756.1234.5678.97, Seefeldstrasse 18, 8008 Zürich."

- The external model receives: "Draft a reminder for `<PERSON_1>`, AHV `<NATIONAL_ID_2>`, `<CH_ADDRESS_3>`."
- The model answers with the placeholders, for example "Dear `<PERSON_1>`, …".
- The user reads "Dear Reto Wyss, …", word by word while the answer streams.

The same value keeps the same placeholder within a request, so the model can still tell people apart. Placeholders that
are already in a question (text a user anonymised by hand) are left as they are and never reused for another value.

## How it works

A guardrail in the LiteLLM gateway (`pii-anonymisation`) handles every chat request:

1. Every text of the conversation (system prompt, questions, earlier answers, tool results, RAG context) goes to the
   self-hosted Presidio analyzer, which finds the personal data. No text leaves the deployment for this.
2. Each value is replaced by a numbered placeholder. Overlapping detections are merged first, so a placeholder is never
   broken.
3. The answer is restored as it arrives: in the text, in the model's reasoning and in tool-call arguments (which stay
   valid JSON). While streaming, only a possible placeholder prefix of a few characters is held back.

If the analyzer cannot be reached, the request is refused with an error instead of being sent unmasked.

## Which calls are anonymised

Every model in the gateway configuration declares where it runs (`model_info.aihub_hosting_location`). Calls to every
model that is not `local` (the Swiss cloud providers and any other external provider) are always anonymised, for every
caller: plain chats, agents (including titles, follow-ups and memory extraction) and bots. Calls to models running
inside the deployment are not anonymised, unless the call asks for it:

```json
{"model": "text-generation/Qwen3-VL-30B-A3B-Instruct-FP8", "guardrails": ["pii-anonymisation"], "messages": []}
```

Only chat requests are anonymised. Embeddings, reranking, transcription and image generation are not.

### Anonymising an agent profile

Every agent profile has an **Anonymise personal data** checkbox at the end of its configuration form, whatever the
blueprint. When it is on, every LLM call of the profile's runs asks for the guardrail, also for models inside the
deployment: the answer, the meta-question check, the title, the follow-ups, the memory extraction, and the runs the
profile delegates to. The answer starts with a short note that personal data was replaced before it reached the
model. Use it for profiles that handle sensitive data, such as HR, even when their models run on premises.

## What is detected

The analyzer runs Presidio with GLiNER's multilingual PII model and patterns for Swiss and international formats, in
German, French, Italian and English:

| Type                                  | Examples                                                                                      |
| ------------------------------------- | --------------------------------------------------------------------------------------------- |
| Person names, addresses, cities       | Reto Wyss, Seefeldstrasse 18, 8008 Zürich                                                     |
| Email addresses, phone numbers, IBANs | +41 44 270 41 87, CH93 0076 2011 6238 5295 7                                                  |
| National IDs                          | AHV numbers; US SSN, UK National Insurance, French NIR, Italian codice fiscale, German tax ID |
| Health data identifiers               | Patient and case numbers, health insurance card numbers                                       |
| Documents and dates                   | Passport and ID card numbers, birth dates                                                     |

Other dates, company names and descriptions that identify a person only through context (a job title together with a
company) are not masked.

Pronouns, roles and field labels ("Sie", "vous", "Benutzer", "Adresse", "IBAN") are never masked, in German,
French, Italian or English, also with a short number ("Position 2", "Art. 5"): the detection model tags them as names or as the type they name, and masking them would
garble the request. The list is `pii_allow_list` in the gateway configuration.

## Checking it in Langfuse

Every call the gateway anonymises leaves a `pii-anonymisation` observation in Langfuse. In an agent run it sits in the
run's trace, next to the step that made the call: its input is the request exactly as the provider received it, with
placeholders, its output says how many values of which type were replaced, and its metadata names the model and why
the call was anonymised (a model outside the deployment, or requested by the call, as with a profile's checkbox). To
see every anonymised call, open Tracing → Observations and search for `pii-anonymisation`. Calls outside an agent run,
such as plain chats, are listed with their counts only. A call refused because the analyzer was unavailable shows as an
error.

The run's other observations are recorded by the agent before the call reaches the gateway, so they show the original
text; Langfuse runs inside the deployment.

## Configuration

::: details Gateway configuration (generated from `litellm-config.yml.j2`):
```yaml
guardrails:
  - guardrail_name: "pii-anonymisation"
    litellm_params:
      guardrail: pii_anonymisation_guardrail.PiiAnonymisationGuardrail
      mode: [pre_call, post_call]
      default_on: false   # the guardrail itself runs on every model that is not `local`
      presidio_language: "de"
      pii_entities_config:
        PERSON: "MASK"
        CH_ADDRESS: "MASK"
        NATIONAL_ID: "MASK"
        # ... the full list is in the template
      pii_allow_list: [sie, ihnen, Benutzer, Adresse, IBAN]   # never masked; full list in the template

model_list:
  - model_name: text-generation/gemma-4-31B-it
    model_info:
      aihub_hosting_location: swiss_cloud   # local | swiss_cloud | eu | global
```

The analyzer URL and key come from `PRESIDIO_ANALYZER_API_BASE` and `PRESIDIO_ANALYZER_API_KEY`. The recognizers are in
`infra/deployment/templates/configs/presidio-analyzer.yaml`; changing them needs `make generate-compose` and a restart
of the analyzer, no image rebuild.
:::

## Limits

- The model has to write placeholders back exactly as it received them. A model that changes them (`<Person_1>`) leaves
  them in the answer.
- Analysis adds time to each request: a few hundred milliseconds for a question, about 50 seconds on CPU for a
  20,000-token prompt such as a long mail thread.
- The patterns for record numbers, insurance cards, ID documents and birth dates were written against synthetic test
  data; check them against your own document formats.
