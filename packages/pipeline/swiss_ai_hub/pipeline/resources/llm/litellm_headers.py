"""
Headers injected into every LiteLLM call originating from a Dagster pipeline.

The pipeline embeds millions of document chunks per run. Storing the prompts and responses
in `LiteLLM_SpendLogs` blew the database past 130 GB with no retrieval value (embedding
inputs are reproducible from the source documents; outputs are vectors). This header
preserves the spend log entry — cost, tokens, model, timing — while dropping the message
content. Chat traffic from agents/users is unaffected because they don't import this.
"""

PIPELINE_REDACTION_HEADERS: dict[str, str] = {"x-litellm-enable-message-redaction": "true"}
