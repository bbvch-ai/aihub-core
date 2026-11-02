---
title: Data anonymization
---

# Data anonymization

The Swiss AI Hub can replace personal data in requests to language models with placeholders, and put the original values
back into the answer before the user sees it. The model never sees a name, an address or an AHV number; the user reads a
normal answer. A deployment turns it on for every model hosted outside it, an agent profile for its own calls.

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

Three switches decide, and any one of them is enough:

| Switch | Who sets it | What it anonymises |
| --- | --- | --- |
| `PII_ANONYMISE_EXTERNAL_MODELS=true` | The operator, per deployment (off by default) | Every call to a model hosted outside the deployment, for every caller: plain chats, agents (including titles, follow-ups and memory extraction) and bots |
| **Anonymise personal data** on an agent profile | The profile's admin | Every call of that profile's runs, whatever the model |
| The [Anonymiser](../../5_agents/14_anonymiser/) agent | Each user, by hand | The text the user sends it |

Every model in the gateway configuration declares where it runs (`model_info.aihub_hosting_location`); every model that
is not `local` (the Swiss cloud providers and any other external provider) counts as outside the deployment. Turn the
deployment switch on when external models may receive personal data that must not leave the organisation. With it off,
plain chats with an external model send their text as it is, and only profiles with the checkbox anonymise. The switch
is read when the gateway starts: change the environment variable and restart `litellm`. A value other than `true` or
`false` counts as `true`, and the gateway logs an error.

A call can also ask for the guardrail itself:

```json
{"model": "text-generation/Qwen3-VL-30B-A3B-Instruct-FP8", "guardrails": ["pii-anonymisation"], "messages": []}
```

Only chat requests are anonymised. Embeddings, reranking, transcription and image generation are not.

::: warning Answers can get worse
The model reasons over placeholders, not values. It cannot tell that two spellings of one value are the same ("Herr
Meier" in the question, "Hans-Peter Meier" in a document, or "Genf" and "Genève" get different placeholders), compute an
age from a masked birth date, or use what it knows about a masked city. Knowledge agents then answer that the
documents hold no answer. Anonymise where the data requires it, not by default.
:::

### Anonymising an agent profile

Every agent profile has an **Anonymise personal data** checkbox at the end of its configuration form, whatever the
blueprint. When it is on, every LLM call of the profile's runs asks for the guardrail, also for models inside the
deployment: the answer, the meta-question check, the title, the follow-ups, the memory extraction, and the runs the
profile delegates to. The answer starts with a short note that personal data was replaced before it reached the model.
Use it for profiles that handle sensitive data, such as HR, even when their models run on premises.

### Anonymising text by hand

Users can also anonymise a text themselves with the [Anonymiser](../../5_agents/16_anonymiser/) agent, then use it in
any tool, inside the Hub or outside it. They paste the answer back into the same chat to get the original values
restored. The Anonymiser uses the same analyzer and the same list of what counts as personal data, and calls no model.

## What is detected

The analyzer runs Presidio with GLiNER's multilingual PII model and patterns for Swiss and international formats, in
German, French, Italian and English:

| Type                                  | Examples                                                                                      |
| ------------------------------------- | --------------------------------------------------------------------------------------------- |
| Person names, addresses, cities       | Reto Wyss, "Name: Brunner", "Frau Gerber", Seefeldstrasse 18, 8008 Zürich                     |
| Email addresses, phone numbers, IBANs | +41 44 270 41 87, CH93 0076 2011 6238 5295 7                                                  |
| National IDs                          | AHV numbers; US SSN, UK National Insurance, French NIR, Italian codice fiscale, German tax ID |
| Health data identifiers               | Patient and case numbers, health insurance card numbers                                       |
| Documents and dates                   | Passport and ID card numbers, birth dates                                                     |

Other dates, company names and descriptions that identify a person only through context (a job title together with a
company) are not masked.

Pronouns, roles, salutations, field and room labels ("Sie", "vous", "Benutzer", "Patientin", "Grüezi", "Adresse",
"IBAN", "Zimmer") are never masked, in German, French, Italian or English, also with a short number ("Position 2",
"Art. 5", "Zimmer 12"): the detection model tags them as names or as the type they name, and masking them would garble
the request. The list is `pii_allow_list` in the gateway configuration.

## Checking it in Langfuse

Every call the gateway anonymises leaves a `pii-anonymisation` observation in Langfuse. In an agent run it sits in the
run's trace, next to the step that made the call: its input is the request exactly as the provider received it, with
placeholders, its output says how many values of which type were replaced, and its metadata names the model and why the
call was anonymised (a model outside the deployment, or requested by the call, as with a profile's checkbox). To see
every anonymised call, open Tracing → Observations and search for `pii-anonymisation`. Calls outside an agent run, such
as plain chats, are listed with their counts only. A call refused because the analyzer was unavailable shows as an
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

## Sizing the analyzer

One analysis takes the same time on any number of CPUs: about 0.5 seconds for a 400-character message, 5 seconds for
4,000 characters and 24 seconds for 20,000. More CPUs let the analyzer serve more calls at once, so users wait less in
the queue. Measured on the default 4 CPUs and with the CPU limit raised to 8:

| Text | Users at once | 4 CPUs: calls/s, median wait | 8 CPUs: calls/s, median wait |
| ------------ | ------------- | ---------------------------- | ---------------------------- |
| 400 chars | 16 | 2.9, 5.4 s | 5.4, 2.9 s |
| 4,000 chars | 16 | 0.29, 41 s | 0.53, 29 s |
| 20,000 chars | 4 | 0.06, 69 s | 0.11, 37 s |

The gateway analyses only what it has not seen: the messages of one call side by side, and every earlier message of a
conversation from a cache. Turn 10 of a chat with a 4,000-character system prompt costs the analyzer under 2 seconds
instead of 25.

Size it in the environment file, then restart the analyzer (and `litellm` for the timeout):

| Variable | Default | What it sets |
| ------------------------------------ | ------- | ---------------------------------------------------------------------- |
| `PRESIDIO_ANALYZER_CPUS` | `4` | CPU limit of the container |
| `PRESIDIO_ANALYZER_MEMORY` | `4G` | Memory limit; each worker holds about 3 GiB |
| `PRESIDIO_ANALYZER_WORKERS` | `1` | Processes, each with its own copy of the models |
| `PRESIDIO_ANALYZER_THREADS` | `4` | Requests one worker analyses at once |
| `PRESIDIO_ANALYZER_TORCH_THREADS` | `2` | CPU threads per analysis |
| `PRESIDIO_ANALYZER_TIMEOUT_SECONDS` | `150` | How long the gateway waits for one analysis before it refuses the call |

Keep workers × threads × torch threads equal to the CPU limit. For 8 CPUs raising `PRESIDIO_ANALYZER_CPUS` to `8` is
enough (1 × 4 × 2). For 16 CPUs use 2 workers and `PRESIDIO_ANALYZER_MEMORY=7G`.

::: warning
Leave the torch threads at 2: with 1, a 20,000-character text takes 85 seconds instead of 24. The gain above 8 CPUs has
not been measured on server hardware yet.
:::

## Limits

- The model has to write placeholders back exactly as it received them. A model that changes them (`<Person_1>`) leaves
  them in the answer.
- Analysis adds time to each request: a few hundred milliseconds for a question, about 50 seconds on CPU for a
  20,000-token prompt such as a long mail thread.
- The patterns for record numbers, insurance cards, ID documents and birth dates were written against synthetic test
  data; check them against your own document formats.
