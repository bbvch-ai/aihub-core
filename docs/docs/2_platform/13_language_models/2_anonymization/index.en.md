---
title: Data anonymization
---

# Data anonymization

The Swiss AI Hub integrates Presidio for detecting and anonymizing personally identifiable information (PII) in user
questions before they reach external LLM providers.

## What Presidio protects

Presidio catches PII that users accidentally include in their questions:

- "Can you review this contract for John Smith (john.smith@company.com)?"
- "What's the policy for credit card 4532-1234-5678-9012?"
- "How do I process the invoice for phone number +41 79 123 45 67?"

Without Presidio, this PII gets sent to external LLM providers (OpenAI, Google) as part of the API request.

## How it works

Presidio runs as a guardrail in the LiteLLM proxy layer. It scans user questions for PII patterns before sending
requests to language models.

Two anonymization modes:

Mask mode replaces detected PII with placeholders like `[PERSON]` or `[EMAIL_ADDRESS]`. The question "Can you review
this contract for John Smith?" becomes "Can you review this contract for [PERSON]?" before reaching the LLM. The model
can still understand context and generate a useful response.

Block mode rejects the entire request when certain PII types appear. Use this for highly sensitive data like credit card
numbers. The user receives an error message instead of a response.

## Supported PII types

Presidio detects person names, email addresses, credit card numbers, phone numbers, social security numbers, IP
addresses, and dates or locations that could identify individuals. Detection uses pattern matching, regular expressions,
and named entity recognition models. The system supports multiple languages including English, German, French, and
Italian.

## Configuration

Presidio guardrails are configured in LiteLLM but disabled by default. Administrators enable them per deployment based
on data sensitivity requirements.

::: details Example guardrail configuration:
```yaml
guardrails:
  - guardrail_name: "presidio-mask-guard"
    litellm_params:
      guardrail: presidio
      default_on: false
      mode: "pre_call"
      presidio_language: "de"
      output_parse_pii: true
      pii_entities_config:
        PERSON: "MASK"
        EMAIL_ADDRESS: "MASK"

  - guardrail_name: "presidio-block-guard"
    litellm_params:
      guardrail: presidio
      default_on: false
      mode: "pre_call"
      pii_entities_config:
        CREDIT_CARD: "BLOCK"
```

Configure which PII types to mask or block through the `pii_entities_config` section. Set `default_on: true` to enable
the guardrail for all requests.
:::

## When to use anonymization

| Scenario                                      | Recommendation                                                       |
| --------------------------------------------- | -------------------------------------------------------------------- |
| External LLM providers (OpenAI, Google, etc.) | Enable Presidio to protect data before it leaves your infrastructure |
| Self-hosted models on-premises                | Optional - your data never leaves your control                       |
| User-generated content                        | Enable if users might accidentally include PII                       |
| Pre-sanitized data                            | Skip Presidio to avoid unnecessary overhead                          |
| Regulatory requirements (GDPR, HIPAA)         | Enable to demonstrate PII protection controls                        |

Presidio applies to all requests when enabled. Use block mode sparingly - only for highly sensitive PII types like
credit cards where you need hard rejection rather than masking.
