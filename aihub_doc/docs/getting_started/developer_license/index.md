---
title: Developer License
index: 3
---

# Extensibility and Licensing

## The AI Hub Developer License

> tldr; The AI-Hub Developer License transforms the platform from a bbv-delivered solution into a strategic asset that clients can own, adapt, and evolve independently. By granting access to the core code and pairing it with training, support, and a flexible architecture, clients can build internal AI expertise, respond quickly to changing market conditions, and maintain the confidence that their private data and custom logic remain under their control.
> 
> This combination of openness, support, and privacy safeguards ensures that the AI-Hub continues to deliver value long after the initial deployment, becoming a cornerstone of the client’s AI strategy.


As the AI-Hub grows and matures, it becomes increasingly valuable as a foundational platform for clients looking to build their own AI capabilities. Rather than treating the AI-Hub as a closed solution, bbv offers a **Developer License**, allowing clients to use the AI-Hub as a base for their internal AI teams. This approach promotes self-sufficiency, reduces long-term dependency on external consultancies, and enables clients to tailor the solution to their evolving business needs.

### What the Developer License Provides

**Access to the AI-Hub Core:**
- Clients gain direct access to the AI-Hub’s core repositories, including the common libraries, infrastructure as code templates, agent codebases, and pipelines.  
- By having full visibility into how agents, pipelines, and the frontend are built, internal teams can learn from best practices, patterns, and architectural decisions made by the AI-Hub team.

**Starting Point for In-House AI Development:**
- Clients can clone the AI-Hub repositories and bootstrap their own AI projects. They can add new agents, define custom workflows, or integrate specialized pipelines without starting from scratch.
- Over time, as their internal AI capabilities mature, clients can extend the AI-Hub with their own libraries, tooling, or domain-specific logic.

**Modular and Extensible Architecture:**
- The Developer License ensures that clients benefit from the AI-Hub’s layered approach, as there is a dedicated section in this documentation that talks more about it, enabling them to override or extend functionalities without losing the ability to merge upstream updates.
- As bbv continues to improve the AI-Hub’s core, clients can pull in these updates to stay current with new best practices, improvements, or efficiency gains.

### Support and Training from bbv

**Initial Onboarding:**
- bbv assists client teams in understanding the AI-Hub’s architecture, guiding them through the concepts of agents, workflows, pipelines, and event-driven communication.
- Workshops and training sessions help internal developers learn how to utilize the AI-Hub Developer License effectively, including setting up local environments, running CI/CD pipelines, and customizing agents.

**Continuous Support:**
- With a Developer License, clients often establish a support agreement with bbv, ensuring that their developers have a senior engineer or consultant available for questions.
- Regular office hours or scheduled support windows allow the client’s team to ask questions, get troubleshooting help, or discuss advanced topics like performance tuning or integrating new AI models.

**Stability and Maintenance:**
- If a key internal developer leaves the client’s organization, the presence of a stable codebase and ongoing support from bbv reduces the risk of knowledge loss.
- bbv can step in to maintain or extend the solution temporarily, bridging any resource gaps and preserving business continuity.

### Protecting Client Privacy and Custom Code

**Project Separation and Architectural Integrity:**
- The AI-Hub architecture enforces a clear separation between the common core and client-specific code. This ensures that sensitive client logic and data handling remain in the client’s private repositories.
- The client’s extensions and configurations are never merged back into the AI-Hub’s core repository, preventing any accidental leakage of proprietary knowledge or logic.

**Private Deployments:**
- Because the client runs the AI-Hub in their own Azure environment or on-premises infrastructure, data never leaves their controlled environment. This complies with privacy laws, data governance policies, and internal security standards.
- Sensitive integrations, like connecting to a client’s internal databases or reading confidential documents, occur solely in the client’s infrastructure. The AI-Hub core code never directly accesses or stores client-specific data.

**License Terms and Boundaries:**
- The Developer License clearly delineates what code and capabilities are provided by bbv and how clients may use them.
- While clients gain the freedom to modify or extend the AI-Hub code, licensing terms ensure that the original intellectual property (like the AI-Hub’s core architecture and common components) is respected.


## 10.2 Adding New Components

> tldr; The AI-Hub was designed to be extensible, ensuring that as AI technologies evolve, the platform can evolve too. By following established guidelines, maintaining consistency, and testing thoroughly, you can add new components, steps, or models without disruption. This approach empowers teams and clients to continuously improve their AI capabilities, adapt to changing requirements, and remain competitive in a rapidly evolving AI landscape.

The AI-Hub’s modular architecture and well-defined interfaces make it straightforward to extend its capabilities. As clients and internal teams gain confidence in the platform, they may want to add new components—be it additional steps in agent workflows, custom I/O managers for pipelines, or support for different AI models. This section outlines guidelines and best practices for introducing these changes without compromising the stability or integrity of the system.

### Extensions to Core Libraries

**Why Extend the Core?**  
- Over time, you might identify common tasks not covered by existing steps or develop specialized logic that could benefit multiple workflows.
- By contributing these enhancements back to the AI-Hub core (or maintaining them in a separate, shared internal library), you ensure that all projects can easily reuse them.

**Guidelines for Contributing:**
1. **Follow Existing Patterns:**  
   Review existing steps, events, or pipeline assets to understand the coding style, naming conventions, and architectural patterns. Consistency is key.
   
2. **Type Annotations and Documentation:**  
   Provide clear type hints, docstrings, and comments. Well-documented code is easier to maintain and integrate.
   
3. **Small, Incremental Additions:**  
   Start by adding a single step or an I/O manager at a time. Test it thoroughly in a local environment and, if applicable, add it to a reference workflow or pipeline.
   
4. **Test and Validate:**  
   Write unit tests to ensure that your new components behave as expected under various conditions. Running these tests in CI guarantees that new additions do not regress over time.
   
5. **Code Reviews and Quality Gates:**  
   All new code should pass the same linting, formatting, and type-checking standards as existing code. Reviewers can provide feedback on API design, naming, or performance considerations.

**Examples of Core Extensions:**
- **New Steps for Agents:** A specialized retrieval step that integrates with a proprietary knowledge base.
- **Additional I/O Managers:** A custom manager for handling a different type of vector store or document storage system.
- **Specialized Event Types:** Introducing a new semantic event type to represent domain-specific data structures, improving clarity and reusability.

### Balancing Control and Innovation

When extending the AI-Hub with new components or models, the guiding principle is to preserve the platform’s integrity while encouraging innovation:
- **Keep Changes Modular:** Avoid mixing unrelated changes in one pull request. Focus on one new feature at a time.
- **Adhere to Quality Standards:** New code should pass all linting, testing, and quality gates.
- **Share Knowledge:** Document new components thoroughly, so other team members or clients can benefit from them.