---
title: Agent evaluations
---

# Agent evaluations

Agent evaluations test and measure AI agent quality before and after deployment. You get data on whether your agents
deliver accurate, complete, and concise responses.

Evaluations test agents against predefined questions with known correct answers. Experiments are run in
[Langfuse](https://langfuse.com), the platform's built-in LLM observability tool. Swiss AI Hub auto-provisions most of
what Langfuse needs — your agents, an agent-calling connection, an evaluator LLM connection, and a prompt template — so
you can focus on three steps:

1. **Create a dataset** of questions and reference answers.
2. **Create evaluators** that score agent responses.
3. **Run experiments** against your agent and review the results.

One thing is not provisioned automatically and must be set once per deployment — see
[Before you start](#before-you-start-set-the-default-evaluation-model).

::: tip
This page describes the Swiss AI Hub workflow only. For Langfuse-specific details (dataset upload formats, evaluator
configuration, experiment comparison), see the [Langfuse documentation](https://langfuse.com/docs).
:::

## Before you start: set the default evaluation model

Langfuse keeps a **project-level default evaluation model** — the judge its managed evaluators use. Swiss AI Hub cannot
provision it: Langfuse exposes no API for this setting. Until a sysadmin sets it, every managed evaluator in the **Run
Experiment** wizard is greyed out and cannot be selected, with the tooltip *"Requires project-level evaluation model"*.

Set it once, after deployment:

1. Open Langfuse and go to **Evaluation → LLM-as-a-Judge → Default Evaluation Model**.
2. Click **Set up** and pick a chat model from the `AI-Hub LLM (Evaluators)` connection.

This is a one-time action per deployment — Langfuse runs a single project for the whole platform, so it does not need
repeating per tenant.

::: tip Upgrading a local environment created before September 2026
Langfuse issues both the agent call and the judge call **from its own container**, so both connections must carry
addresses reachable from there. `.env.dev` now ships them, but an `.env` copied before that change does not. Add:

```bash
LITE_LLM_PROXY_INTERNAL_BASE_URL='http://litellm:4000'
AIHUB_OPENAI_API_BASE_URL='http://host.docker.internal:8000/api/v1/active/openai'
```

Without them the API refuses to register the connections at startup, logging an error that names the missing setting —
the host-side defaults point at `localhost`, which inside the Langfuse container is Langfuse itself.
:::

## 1. Create a dataset

Datasets are collections of test questions with reference answers. Cover representative questions your agent will
receive, include clear reference answers and edge cases. Start with at least 10 question-answer pairs; 20-50 work
better.

You can create a dataset in two ways:

- **In the Swiss AI Hub Admin UI** — open `Datasets`, provide a name and description, add your question-answer pairs,
  then save.
- **In Langfuse** — create the dataset directly, for example by uploading a CSV file with one row per question-answer
  pair.

Either way the dataset is stored in Langfuse and immediately available for experiments.

![Dataset Overview](../../../media/evaluation/dataset_overview.png) *Dataset overview in the Admin UI*

![Creating a Dataset](../../../media/evaluation/dataset_create.png) *Adding test questions with reference answers*

::: warning Datasets created in the Admin UI are append-only
When editing in the Admin UI you can add new question-answer pairs at any time, but you cannot remove or edit items once
saved. To change a question, add a corrected item or edit the dataset in Langfuse.
:::

## 2. Create evaluators

Evaluators score each agent response, typically using LLM-as-a-judge. Configure them in Langfuse. Swiss AI Hub
provisions a dedicated evaluator LLM connection (`AI-Hub LLM (Evaluators)`), so judge models are available out of the
box. Document-extraction models (OCR and vision-language) are deliberately left out of that list — LiteLLM reports them
as chat models, but they cannot grade text.

Recommended dimensions to score:

| Metric       | What it measures                                                                                              |
| ------------ | ------------------------------------------------------------------------------------------------------------- |
| Correctness  | Factual accuracy compared to the reference answer. Free of misinformation, hallucinations, or contradictions. |
| Completeness | Addresses all parts of the query, including multi-part questions and implicit needs.                          |
| Conciseness  | Efficient and direct. Avoids irrelevant tangents, redundancy, or excessive filler.                            |

## 3. Run experiments

Open a dataset card in the Admin UI and click **Run Experiments** to jump to the dataset in Langfuse, then create an
experiment there:

- **Select the agent to test.** Online agents appear automatically as selectable models, named
  `<agent_class>/<agent_id>` — Swiss AI Hub continuously syncs running agents to Langfuse, so no manual registration is
  needed.
- **Use the `ai-hub-agent` prompt template.** This auto-provisioned template maps each dataset question to a request
  against the agent's OpenAI-compatible endpoint, so Langfuse calls your real agent through the platform.
- **Attach the evaluators** from step 2 and run the experiment.

Run experiments before deploying a new agent, after significant changes to its configuration or knowledge base, and
regularly for quality monitoring. Every run is stored in Langfuse, so you can compare runs side-by-side to confirm a
change improved quality.

When interpreting results: low correctness usually points to knowledge base gaps or retrieval issues, low completeness
to missed parts of multi-part questions, and low conciseness to overly verbose responses. Adjust the agent's knowledge
base, system prompts, or retrieval settings accordingly, then re-run to verify improvements.

## What's not implemented

The following features are not currently implemented:

- Bias monitoring and model drift detection: No automated bias detection, fairness metrics, or drift detection. Langfuse
  experiments and OpenTelemetry tracing provide foundational capabilities that could be extended.

- Production A/B testing: No integrated traffic splitting or parallel testing of agent variants in production.
  Pre-deployment comparison via Langfuse experiments is supported.
