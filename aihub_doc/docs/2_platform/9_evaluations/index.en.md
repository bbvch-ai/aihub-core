---
title: Agent Evaluations
index: 9
---

# Agent Evaluations

Agent evaluations provide systematic testing and quality measurement for AI agents before and after deployment. This
ensures your agents deliver accurate, complete, and professional responses to users.

Evaluations test your agents against predefined questions with known correct answers. Think of it as a standardized test
for your AI agents—you provide the questions and expected answers, and the system measures how well your agent performs.

::: info Key Benefits
- **Quality Assurance**: Verify agent performance before and after deployment.
- **Objective Metrics**: Get measurable scores instead of subjective opinions.
- **Continuous Monitoring**: Track quality improvements or regressions as you update your agent's knowledge base and prompts.
- **Compliance Documentation**: Maintain audit trails for regulatory requirements.
:::

## Understanding Datasets

Datasets are collections of test questions with reference answers. Each dataset represents a specific testing scenario
for your agent.

A **good dataset** should cover representative questions your agent will actually receive and include clear, accurate reference answers. It's also important to add edge cases to test robustness. Aim for at least 10 question-answer pairs, though 20-50 is ideal for sufficient coverage.

::: details **Example Dataset Structure**
- Question: "How do I reset my password?"
- Reference Answer: "Click 'Forgot Password' on the login page, enter your email, and follow the reset link sent to your
inbox."
:::

**Creating Datasets**

You can create datasets through the AI-Hub web interface or API:

1.  **Navigate to Evaluations**: Access the evaluation service from the main navigation (e.g., under `Services > Evaluations`).
2.  **Create New Dataset**: Provide a name and description.
3.  **Add Test Questions**: Enter questions and their expected answers.
4.  **Save Dataset**: Your dataset is now ready for experiments.

![Dataset Overview](../../../media/evaluation/dataset_overview.png)
*The dataset overview page shows all your evaluation datasets with creation dates*

![Creating a Dataset](../../../media/evaluation/dataset_create.png)
*Add new test questions with expected answers directly in the web interface*

::: tip Best practice
Start with 20-30 questions covering both simple and complex scenarios. You should update your datasets as your agent's capabilities evolve and organize them by topic or use case for easier management.
:::

## Running Experiments

Experiments test your agent against a dataset and produce quality scores.

**How to Run an Experiment:**

1.  **Select Agent**: Choose which agent to evaluate.
2.  **Choose Dataset**: Pick an appropriate test dataset.
3.  **Start Experiment**: The system automatically runs all tests.
4.  **Review Results**: View scores and detailed analysis.

![Creating an Experiment](../../../media/evaluation/experiment_create.png)
*To create an experiment, select the agent and the dataset you want to test it against.*

![Experiment Overview](../../../media/evaluation/experiment_overview.png)
*The overview page lists all past experiments and their high-level average scores.*

![Running an Experiment](../../../media/evaluation/experiment_running.png)
*While an experiment is running, you can see its progress.*

You should **run experiments** before deploying a new agent to production, after making significant changes to its configuration or knowledge base, and regularly (e.g., weekly or monthly) for continuous quality monitoring.

### How it Works: AI Judges

**During an experiment**, each question from the dataset is sent to your agent. The agent's response is captured and then evaluated by **three independent AI judges**.

These "judges" are themselves an advanced LLM, tasked with assessing your agent's response against the provided reference answer. Using three judges provides a more robust and nuanced score, reducing the bias of a single evaluation. The results are then averaged and displayed in the evaluation interface.


### Evaluation Metrics

The AI judges score each response against these three key dimensions. The descriptions below provide insight into what the judges are looking for.

| Metric | Description | Scoring Guide (0.0 - 1.0)                                                                                    |
| :--- | :--- |:-------------------------------------------------------------------------------------------------------------|
| **Correctness** | Is the agent's response factually accurate **when compared to the reference answer**? The response should be free of misinformation, hallucinations, or contradictions. | **1.0:** Perfect (matches reference)<br/>**0.5:** Partial (some errors)<br/>**0.0:** Wrong (misleading)      |
| **Completeness** | Does the response fully address **all parts of the user's query**? This includes handling multi-part questions or implicit needs, not just the most obvious part. | **1.0:** Complete (all parts answered)<br/>**0.5:** Partial (some aspects missed)<br/>**0.0:** Incomplete    |
| **Conciseness** | Is the response efficient and to the point? It should avoid **irrelevant tangents, redundancy, or excessive conversational filler** that doesn't directly help answer the user's question. | **1.0:** Perfect (to the point)<br/>**0.5:** Verbose (a bit wordy)<br/>**0.0:** Excessive (unnecessary info) |

**Interpreting Scores (General Guidelines)**

These score thresholds are **not absolute rules**, but rather **interpretive guidelines** to help you quickly assess performance. A score of 0.79 isn't necessarily a failure, and 0.81 isn't perfect. Use these ranges to orient your analysis:

- **Score > 0.8 (Excellent):** Indicates the agent is consistently reliable, accurate, and ready for production.
- **Score 0.6 - 0.8 (Good):** Suggests the agent performs well, but may have minor issues with consistency, completeness, or verbosity. Review failing test cases for patterns.
- **Score < 0.6 (Needs Attention):** Signals potential significant issues. You should review these responses closely to identify a root cause before deployment.

### Viewing Results

After an experiment completes, you can view detailed results showing both overall performance and individual question scores.

![Experiment Results](../../../media/evaluation/experiment_result.png)
*The results view displays overall metric scores and a detailed breakdown for each test question*

The results page shows star ratings for the three evaluation metrics at the top, with a detailed table below. Each row in the table represents one test question, showing the question itself, the reference answer, your agent's actual response, and individual scores for correctness, completeness, and conciseness. Response latency is also tracked.

You can expand individual questions to see the full text and analyze patterns. Low correctness scores typically indicate knowledge base gaps or retrieval issues. Low completeness scores suggest the agent isn't fully addressing multi-part questions. Low conciseness scores point to overly verbose responses.

Based on your results, you can update your agent's knowledge base, refine system prompts, or adjust retrieval settings. Run the experiment again after making changes to verify improvements.

::: tip For Advanced Analysis
Phoenix (the underlying evaluation platform) can optionally be accessed for deeper technical investigation, including full conversation traces and raw telemetry data. However, all essential evaluation information is available in the standard AI-Hub interface.
:::