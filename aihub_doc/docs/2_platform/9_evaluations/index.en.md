---
title: Agent evaluations
---

# Agent evaluations

Agent evaluations test and measure AI agent quality before and after deployment. You get data on whether your agents
deliver accurate, complete, and concise responses.

Evaluations test agents against predefined questions with known correct answers. You provide the questions and expected
answers, and the system measures how well your agent performs.

Benefits of evaluations:

- Verify agent performance before and after deployment
- Get measurable ratings instead of subjective opinions
- Track quality changes as you update knowledge bases and prompts
- Maintain audit trails for regulatory requirements

## Datasets

Datasets are collections of test questions with reference answers.

Cover representative questions your agent will receive. Include clear, accurate reference answers and edge cases. Start
with 10 question-answer pairs minimum. 20-50 pairs work better.

::: details Example dataset structure
- Question: "How do I reset my password?"
- Reference Answer: "Click 'Forgot Password' on the login page, enter your email, and follow the reset link sent to your
  inbox."
:::

To create a dataset, navigate to the evaluation service (under `Services > Evaluations`), provide a name and
description, add questions and expected answers, then save.

![Dataset Overview](../../../media/evaluation/dataset_overview.png) *Dataset overview showing all evaluation datasets
with creation dates*

![Creating a Dataset](../../../media/evaluation/dataset_create.png) *Adding test questions with expected answers*

::: tip
Start with 20-30 questions covering simple and complex scenarios. Update datasets as your agent evolves. Organize by
topic or use case.
:::

## Running experiments

Experiments test your agent against a dataset and produce quality ratings.

To run an experiment, select an agent, pick a test dataset, start the experiment, then review the ratings and analysis.

![Creating an Experiment](../../../media/evaluation/experiment_create.png) *Creating an experiment by selecting an agent
and dataset*

![Experiment Overview](../../../media/evaluation/experiment_overview.png) *Experiment overview listing past experiments
\- click for details*

![Running an Experiment](../../../media/evaluation/experiment_running.png) *Experiment progress during execution*

Run experiments before deploying a new agent, after making significant changes to configuration or knowledge base, and
regularly (weekly or monthly) for quality monitoring.

### How AI judges work

Each question gets sent to your agent. Three AI judges (LLMs) evaluate the response against the reference answer.
Results are averaged and displayed as star ratings.

### Evaluation metrics

Three metrics, rated 0-5 stars:

| Metric       | Description                                                                                                   | Rating Guide                                                       |
| ------------ | ------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------ |
| Correctness  | Factual accuracy compared to the reference answer. Free of misinformation, hallucinations, or contradictions. | 5: Matches reference<br/>3: Some errors<br/>0: Wrong/misleading    |
| Completeness | Addresses all parts of the query, including multi-part questions and implicit needs.                          | 5: All parts answered<br/>3: Some aspects missed<br/>0: Incomplete |
| Conciseness  | Efficient and direct. Avoids irrelevant tangents, redundancy, or excessive filler.                            | 5: To the point<br/>3: Verbose<br/>0: Excessive                    |

Rating ranges:

- 4-5 stars: Ready for production.
- 3-4 stars: Works well but may have minor issues. Review failing test cases.
- Below 3 stars: Review closely before deployment.

### Viewing results

![Experiment Results](../../../media/evaluation/experiment_result.png) *Experiment results showing overall metrics and
detailed breakdown per question*

The results page shows star ratings for the three metrics at the top. Below is a table with each test question,
reference answer, agent's response, ratings, and response latency.

Expand questions to see full text. Low correctness ratings usually mean knowledge base gaps or retrieval issues. Low
completeness ratings suggest the agent misses parts of multi-part questions. Low conciseness ratings mean overly verbose
responses.

Update your agent's knowledge base, system prompts, or retrieval settings based on results. Run the experiment again to
verify improvements.

::: tip
Langfuse can be accessed for deeper investigation, including conversation traces, cost attribution, and raw telemetry
data. In development, access Langfuse at `http://localhost:6006`.
:::

## What's not implemented

The following features are not currently implemented:

- Bias monitoring and model drift detection: No automated bias detection, fairness metrics, or drift detection. The
  evaluation framework and OpenTelemetry tracing provide foundational capabilities that could be extended.

- Production A/B testing: No integrated traffic splitting or parallel testing of agent variants in production.
  Pre-deployment comparison via experiments is supported.
