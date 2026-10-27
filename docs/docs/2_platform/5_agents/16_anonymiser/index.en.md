---
title: Anonymiser
description: Replaces personal data in a text with placeholders so you can use it in any tool, and puts the original values back into the answer. No AI model sees your text.
---

# Anonymiser

The **Anonymiser** lets users anonymise a text themselves. They send it a text and get it back with names, addresses,
AHV numbers and other personal data replaced by placeholders such as `<PERSON_1>`. They can paste that into any other
agent, chat or external tool, then paste the answer back into the same chat and get it with the original values
restored.

It calls no language model. The text goes only to the deployment's own Presidio analyzer, the one the gateway uses for
[data anonymization](../../13_language_models/2_anonymization/), so nothing the Anonymiser handles leaves the
deployment.

## What users see

1. A user sends: "Please write to Reto Wyss, Seefeldstrasse 18, 8008 Zürich, about his AHV 756.1234.5678.97."
2. The Anonymiser answers with the text in a copyable block: "Please write to `<PERSON_1>`, `<CH_ADDRESS_2>`, about his
   AHV `<NATIONAL_ID_3>`."
3. The user pastes that into another tool and gets an answer such as "Dear `<PERSON_1>`, …".
4. The user pastes the answer back into the same Anonymiser chat and gets "Dear Reto Wyss, …".

The chat decides the direction per message: a message that contains placeholders this chat issued is restored, anything
else is anonymised.

- **Stable placeholders.** A value keeps its placeholder for the whole chat, so Reto Wyss is `<PERSON_1>` in every
  message, and restoring works however many turns later.
- **One chat, one mapping.** A chat restores only the placeholders it issued itself. A new chat cannot restore another
  chat's placeholders.
- **Foreign placeholders are pointed out.** Placeholders the chat never issued are left as they are, and the answer
  lists them.
- **No title from the content.** The chat is titled "Anonymised text", so the chat list never shows the personal data.

## What it deliberately leaves out

| Capability                                       | Anonymiser |
| ------------------------------------------------ | :--------: |
| Language model calls (answer, title, follow-ups) |     ❌     |
| User or organization memory                      |     ❌     |
| Attached files and images                        |     ❌     |
| Knowledge references (`#`)                       |     ❌     |

Only the text of the message is anonymised. To anonymise what an agent sends to its model automatically, use the
**Anonymise personal data** checkbox on its profile instead (see
[Anonymising an agent profile](../../13_language_models/2_anonymization/#anonymising-an-agent-profile)).

## Configuration reference

A profile needs only its identity: ID, name, description and icon. What counts as personal data is the same list the
gateway uses, so a text anonymised by hand and a request the gateway anonymises mask the same things.

The deployment runs the blueprint as the `anonymiser_agent` service, which reaches the analyzer through the
`pii-detection` network with `PRESIDIO_ANALYZER_API_BASE` and `PRESIDIO_ANALYZER_API_KEY`. It has no LiteLLM access.

## Limits

- The mapping is kept with the chat's agent state, so it holds personal data the way the chat history does.
- The other tool has to write the placeholders back exactly as it received them. A tool that changes them (`<Person_1>`)
  leaves them in the restored text.
- Detection has the same limits as the gateway's; see
  [What is detected](../../13_language_models/2_anonymization/#what-is-detected).
