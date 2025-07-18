---
title: Agent Philosophy
index: 3
---

# Agent Philosophy and Best Practices

## 🌊 AI Agents as Structured Workflows

::: tip TL;DR
Our core philosophy is to build AI agents as **structured workflows**, not as monolithic, open-ended black boxes. This approach combines the deterministic control of traditional software with the reasoning power of AI. By breaking down complex tasks into a series of clear, testable steps, we ensure our agents are transparent, auditable, and reliable. This allows for an incremental journey from tightly controlled logic toward increasingly autonomous and intelligent solutions, without ever relinquishing oversight.
:::

The key to bridging the gap between traditional software and truly intelligent systems lies in how we conceptualize and build AI agents. Instead of giving an agent a high-level goal and hoping for the best, we design them as **step-by-step workflows**. Each workflow is composed of clearly defined steps and transitions, allowing us to maintain transparency, ensure quality, and carefully balance the agent’s autonomy.

### 🤖 Workflows vs. Open-Ended Agents

::: danger The Pitfall of Open-Ended Agents
In traditional software, every action is predefined, leaving no ambiguity but struggling with complexity. In contrast, an open-ended AI agent given a vague goal like "Answer support emails" must decide entirely on its own how to proceed. This can lead to unpredictable behavior, such as attempting useless actions, violating business rules, or getting stuck in infinite reasoning loops.
:::

::: info The Power of the Workflow Model
By treating the agent as a workflow, we deconstruct a large task into smaller, manageable sub-steps. For example, processing a support email might involve distinct steps for classifying the intent, retrieving relevant documents, drafting a response, and checking for compliance. This structure provides clear benefits:

-   **Testability:** Each sub-step can be tested and validated independently, ensuring the reliability of the entire process.
-   **Traceability:** The workflow is visible and auditable from start to finish, helping developers and auditors understand exactly why the agent took a certain action.
-   **Enforced Order:** Critical business logic, like requiring a compliance check before sending a communication, can be hard-coded into the workflow sequence.
:::



## ⚙️ Workflow Design Best Practices

Effective workflow design is crucial for building robust and scalable agents. By following these best practices, you can create systems that are modular, transparent, and easy to maintain.

### Defining Clear Steps and Agents

-   **Single Responsibility per Step:** Each step should accomplish one logical task, like document retrieval, classification, or verification. Avoid combining multiple actions into a single step to simplify debugging and testing.
-   **Typed Input/Output Events:** Use events with clear, consistent schemas. Typed events not only guide the agent's logic but also provide immediate clarity on the data flowing through the workflow, making it easier to understand and maintain.
-   **Agent Composition:** For complex tasks, compose multiple specialized agents rather than building one monolithic agent. For instance, one agent could handle retrieval (RAG), another could enforce business rules, and a third could generate the final response. This modular approach enhances clarity and scalability.

### Ensuring Transparency and Traceability

-   **Use Semantic Events:** Enrich the workflow with meaningful domain information through semantic events. They clarify *why* an agent made a certain decision, dramatically improving explainability for developers and auditors.
-   **Comprehensive Logging:** Combine OpenTelemetry traces with event logs to reconstruct the agent's entire decision-making path. This is essential for debugging, identifying bottlenecks, and justifying outcomes.
-   **Isolated and Integrated Testing:** Test each step independently with mock events to ensure its correctness. Complement this with end-to-end integration tests that simulate a full user query flowing through the entire workflow to verify the final result.



## ⚖️ The Path to Autonomy: A Gradual Approach

Our philosophy isn't to replace human intelligence or override established business logic, but to **augment** it. We achieve this by balancing the raw intelligence of AI reasoning with strict operational controls embedded in the workflow, allowing for a gradual and safe increase in autonomy.

### Start with Strict Control

Initially, workflows should be highly constrained to build trust and verify correctness.
-   **Defined Steps & Allowed Tools:** Each step explicitly outlines what the agent can do (e.g., “classify email,” “access vector database”). The agent cannot spontaneously perform actions outside these predefined possibilities.
-   **Human-in-the-Loop (HITL):** For critical actions, incorporate a mandatory human approval step. As confidence in the agent's reliability grows, these HITL steps can be relaxed or removed.

### Progressive Relaxation and Trust Building

As the agent proves its reliability through extensive testing and monitoring, you can begin to loosen constraints and grant more freedom.

1.  **Introduce Choice Points:** Allow the agent to select from a predefined set of tools or paths. For instance, an agent might choose between two different retrieval strategies based on the query's nature.
2.  **Monitor Performance:** Carefully track metrics like response accuracy, latency, and user satisfaction after granting more autonomy. Positive trends justify further relaxation, while negative trends signal a need to re-tune constraints.
3.  **Periodic Reviews:** Regularly review workflows with stakeholders to confirm that the current level of autonomy meets business needs and that traceability remains sufficient for audits and compliance.

This phased approach ensures your organization can introduce AI with minimal risk, retaining full control while steadily embracing more sophisticated and self-directed AI behaviors.



## 🛡️ Data Handling, Security, and Guardrails

As agents work with sensitive business data, ensuring privacy, security, and correctness is paramount. Our architecture and best practices are designed to deliver trustworthy, auditable, and value-driven results.

### Privacy and Security by Design

-   **Client-Controlled Infrastructure:** By deploying the system in the client’s own Azure environment, data never leaves their network boundaries. Access is governed by the client’s existing Role-Based Access Control (RBAC) policies.
-   **Encryption and Key Management:** All data at rest is encrypted, and communications between services are protected with TLS. Credentials and API keys are stored securely in Azure Key Vault.
-   **Auditability:** Every event in a workflow is timestamped, typed, and logged, providing a robust audit trail for compliance and governance.

### Guardrails and Hallucination Prevention

Large Language Models (LLMs) can occasionally produce plausible-sounding but incorrect answers, known as "hallucinations." Guardrails are essential for ensuring reliability and maintaining user trust.

1.  **Retrieval-Augmented Generation (RAG):** Grounding answers in retrieved documents is the most effective way to reduce hallucinations. The agent's workflow ensures that any generated answer is based on factual information from approved sources. If no relevant document is found, the agent is designed to state that it cannot answer, rather than guessing.
2.  **Context Validation:** Before producing an answer, the agent confirms it has sufficient and relevant context. This prevents it from making assumptions or fabricating details.
3.  **Verification Steps:** After an agent drafts an answer, a separate verification step can run to compare its claims against the source documents. If contradictions arise, the agent can adjust its response or escalate it to a human.
4.  **Approved Tools Only:** Agents operate strictly within their defined workflow. They can only use approved tools and steps, which prevents them from executing unintended or harmful actions.



## 🎯 Use Cases in Action

These principles translate into powerful, practical solutions that save time, reduce complexity, and improve organizational agility.

### 🏥 The FMH Example: Coordinating Multiple Agents for Tariff Support

-   **Context:** The FMH (Swiss Medical Association) issues complex medical tariffs and rules. Medical staff need quick, accurate answers to questions about billing procedures and changes between tariff versions.
-   **Solution:** We built a multi-agent system to handle inquiries.
    -   A **RAG Agent** retrieves conceptual explanations from a handbook.
    -   A **Rules Agent** checks specific billing combinations against a technical database.
    -   A **Coordinating Agent** routes queries to the appropriate specialist agent, or combines their outputs for complex questions.
-   **Outcome:** Users get fast, accurate, context-rich answers, blending high-level understanding with precise technical validation.

### 🏦 Beyond Chatbots: Autonomous Regulatory Monitoring

AI agents aren't limited to responding to user queries. They can also act autonomously when triggered by external events.
-   **Context:** A private bank must monitor and adapt to frequent regulatory updates from sources like FINMA.
-   **Solution:** An autonomous agent is configured to monitor newsletters and official announcements. When a new update is detected, the agent initiates a workflow:
    1.  **Relevance Check:** Determines if the update impacts the bank.
    2.  **Impact Analysis:** Identifies which internal guidelines are affected.
    3.  **Proposal Generation:** Drafts suggested amendments to internal documents to ensure compliance.
    4.  **Human Review:** Notifies a compliance officer to review and approve the changes.
-   **Outcome:** The agent transforms a manual, time-consuming task into an automated, efficient process. It proactively filters noise and delivers actionable insights, demonstrating how autonomy can be introduced safely with a human-in-the-loop.