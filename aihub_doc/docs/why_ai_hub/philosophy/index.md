---
title: Philosophy
index: 2
---

# Core Concepts and Philosophy

## AI Agents as Workflows

> tldr; By framing AI agents as structured workflows, the AI-Hub empowers developers and enterprises to harness the benefits of AI reasoning without relinquishing oversight. This structured approach preserves testability, traceability, and compliance, allowing for an incremental journey from tightly controlled, step-by-step logic toward increasingly autonomous and intelligent solutions.

In there is a dedicated section in this documentation that talks more about it, we explored why AI agents are essential to bridging the gap between traditional software solutions and more intelligent, adaptive systems. Now, we turn our attention to a fundamental principle that guides how these agents are conceptualized and implemented within the AI-Hub: **treating AI agents as structured workflows.**

Rather than building agents as monolithic, open-ended entities that attempt to solve problems with minimal guidance, the AI-Hub encourages the design of agents as **step-by-step workflows.** Each workflow is composed of clearly defined steps and transitions, combining the strengths of algorithmic determinism with the flexibility and intelligence of AI-driven reasoning. This approach allows us to maintain transparency, ensure quality, and carefully balance the agent’s autonomy.

### Workflows vs. Open-Ended Agents

**The Case for Structured Logic:**
- **Traditional Software:** In a conventional algorithmic solution, every action is predefined. The code instructs the system exactly how to handle a given input, leaving no ambiguity. However, these solutions struggle with complex or ambiguous tasks where the instructions cannot easily be exhaustively defined.
- **Open-Ended AI Agents:** Imagine an agent given a high-level goal (e.g., “Answer support emails”). Without structure, the agent must decide entirely on its own how to achieve this, potentially leading to unpredictable, non-transparent behavior. It might repeatedly attempt useless actions, fail to follow business rules, or get stuck in infinite reasoning loops.

**Introducing the Workflow Model:**
- By **treating the agent as a workflow**, we break down a task into smaller, testable sub-steps. For example, if the agent must process a support email, one step could determine the relevant department, another step could draft a response, yet another could check for compliance with internal policies.
- **Benefits:**
  - **Testability:** Each sub-step can be tested and validated independently, ensuring reliability.
  - **Traceability:** The entire workflow is visible and auditable, helping developers understand why the agent took a certain action.
  - **Enforced Order:** Some operations should always happen before others. By defining a workflow, we ensure that these rules are consistently followed.

**Incremental Autonomy:**
- Instead of setting the agent loose in an open world, the workflow ensures that it moves from one well-understood step to the next. Over time, certain steps can become more flexible—allowing the agent to choose the best path out of several alternatives—without losing the safety net of a predefined structure.

For a more detailed technical dive into how these workflows are defined and implemented, refer to there is a dedicated section in this documentation that talks more about it.

### Balancing Control and Intelligence

The AI-Hub’s philosophy is not to replace human intelligence or override established business logic, but to **augment** it. We achieve this by balancing the raw intelligence of language models and AI reasoning with strict operational controls embedded in the workflow design.

**Strict Control Mechanisms:**
- **Defined Steps & Allowed Tools:** Each workflow step outlines what the agent can do at that stage (e.g., “classify the email,” “access the vector database,” or “send a notification”). The agent cannot spontaneously perform actions outside these defined possibilities.
- **Reversible Constraints:** Initially, workflows might be highly constrained, allowing minimal leeway for the agent to improvise. As confidence in the agent grows—thanks to extensive testing and proven reliability—these constraints can be loosened, granting the agent more freedom.

**Gradual Introduction of Autonomy:**
- **Phase One (Highly Constrained):** The agent follows a strict path. Even though it uses AI for reasoning (like classifying inputs), the sequence of steps and the tools it can use are fully predefined. This phase allows building trust and verifying correctness.
- **Phase Two (Selective Relaxation):** After demonstrating reliability, some workflow steps gain flexibility. The agent can choose among multiple paths or tools, applying its reasoning capabilities more autonomously. However, top-level control—such as mandatory approval steps—can still be maintained if desired.

**Outcome:**
- This balance ensures that the organization introducing AI agents can do so with minimal risk. They retain transparency, control, and the ability to audit the agent’s decisions, while steadily embracing more sophisticated, efficient, and self-directed AI behaviors over time.


## Use Cases and Example Projects

> tldr; The FMH and private bank examples demonstrate the adaptability and power of AI agents within the AI-Hub framework:
> 
> - **FMH Tariff Support:** Showcases how multiple specialized agents can coordinate, each focusing on a distinct subproblem—conceptual explanations vs. technical rule checks—and deliver integrated solutions.
> - **Private Bank Autonomy:** Illustrates that agents can operate beyond traditional chatbot use cases, proactively responding to events and assisting with compliance and process updates, gradually increasing autonomy as trust is earned.   
>
> These real-world scenarios ground the theoretical principles described in previous sections. They provide a tangible view of how workflows, controlled autonomy, and step-by-step reasoning translate into practical solutions that save time, reduce complexity, and improve organizational agility.


Throughout the earlier sections—there is a dedicated section in this documentation that talks more about it and there is a dedicated section in this documentation that talks more about it—we established the conceptual reasons for employing AI agents and introduced the idea of structuring them as workflows (there is a dedicated section in this documentation that talks more about it). To further solidify these concepts, it is useful to explore concrete examples where multiple agents come together to solve business problems and go beyond simple chatbot interactions.

In this section, we highlight two illustrative scenarios: one involving **the FMH (Swiss Medical Association) and their tariff support tasks**, and another showcasing how agents can autonomously handle **regulatory updates in a private bank**. These examples underscore the practicality and adaptability of the AI-Hub’s approach, demonstrating that AI agents can tackle domain-specific challenges and autonomously take action when triggered by external events.

### The FMH Example: Coordinating Multiple Agents for Tariff Support

**Context:**
- The FMH issues medical tariffs, essentially lists of billable medical services, along with detailed rules and regulations on how these services can be charged.
- When a new tariff is introduced, medical professionals and administrative staff must learn how to apply it correctly and understand what has changed from older versions.

**Challenge:**
- Previously, this meant combing through lengthy handbooks or complex databases, and navigating rules that may not be straightforward.
- The FMH anticipates a surge in inquiries: questions like “How do I bill position X alongside position Y?” or “What changed from the old tariff to the new one?”

**Solution with AI-Hub Agents:**
- **RAG (Retrieval Augmented Generation) Agent:** One agent focuses on a large handbook, which has been parsed and indexed into a vector database for semantic retrieval.  
  - When a user asks a question about why a certain rule exists or what changed conceptually, this agent fetches relevant sections from the handbook and reconstructs a coherent answer, providing context and justifications.
- **Rules Agent:** Another agent specializes in the tariff’s technical rules. For a given tariff position (e.g., a specific billing code), it can look up the allowed combinations, constraints, and limits.  
  - For instance, if a user asks, “Can I bill these two positions together?” the rules agent accesses the tariff database to find the applicable rule sets and returns the correct billing logic.

**Coordination Between Agents:**
- A **coordinating agent** may sit on top, taking user queries and deciding which sub-agent should handle the request first.  
- If a question involves both conceptual understanding (from the handbook) and specific rule checking (from the tariff database), the coordinating agent orchestrates a sequence: first calling the RAG agent to provide context, then the rules agent to verify billing constraints.

**Outcome:**
- By modeling the solution as multiple specialized agents working in a well-defined workflow, the system can handle a wide range of queries—from high-level conceptual explanations to detail-oriented rule validations.
- End-users benefit from accurate, context-rich answers that save time and reduce the need for manual research.

### Beyond Chatbots: Autonomy Triggered by Real-World Events

While the FMH example primarily shows agents responding to user queries, AI agents aren’t limited to a request-response pattern. They can also act autonomously, triggered by external events. Consider a **private bank scenario** where compliance with financial regulations is paramount.

**Private Bank Regulatory Updates Scenario:**
- The bank must stay updated with changes in FINMA regulations and other reputable advisory sources like Big Four firms.
- These updates arrive in the form of newsletters, published notices, or website announcements.
- Without automation, a human might read through these notices daily, filter out irrelevant information, and adapt internal guidelines or highlight areas needing review.

**Implementing an Autonomous Agent:**
- An AI agent can be configured to monitor incoming newsletters, RSS feeds, or direct FINMA updates. (Later sections will detail how pipelines feed data into the system, but conceptually, the agent can receive an event like “New FINMA newsletter arrived.”)
- Upon receipt of this event, the agent:  
  1. **Relevance Check:** Determines if the update pertains to the bank’s specific business scope.  
  2. **Rule Mapping:** Identifies which internal guidelines may be impacted.  
  3. **Proposal Generation:** Drafts suggested amendments to the bank’s internal documents to align with the new regulations.
- If necessary, the agent can inform a human compliance officer, who then reviews the suggested changes. This “human-in-the-loop” dynamic ensures quality control while still leveraging the agent’s ability to filter and transform raw updates into actionable insights.

**Key Takeaways:**
- This scenario goes beyond simple Q&A. The agent autonomously acts upon triggers (newsletters, website checks), initiating updates and producing actionable outputs without waiting for a human request.
- Over time, trust can be built, allowing the agent greater autonomy—perhaps even automating routine updates. This expansion of autonomy aligns with the philosophy discussed in there is a dedicated section in this documentation that talks more about it.