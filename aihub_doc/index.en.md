---
# https://vitepress.dev/reference/default-theme-home-page
layout: home

hero:
  name: Swiss AI Hub
  text: The open AI platform you own and control
  tagline: Complete infrastructure for production AI. Deploy in your data center. Build with confidence. Keep your data in Switzerland.
  actions:
    - theme: alt
      text: Our Vision
      link: /docs/1_vision_and_positioning/1_introduction/
    - theme: alt
      text: Why Swiss AI Hub
      link: /docs/1_vision_and_positioning/1_introduction
    - theme: brand
      text: Platform Overview
      link: /docs/2_platform/2_architecture/1_core_components/

features:
  - title: The open-source AI bet
    details: Best-in-class open-source tools (LiteLLM, Milvus, LlamaIndex) integrated and ready. When they evolve, you benefit. No vendor lock-in, no licensing fees, no platform constraints. Bet on the ecosystem, not a single vendor.
  - title: Own the platform, not rent it
    details: Complete infrastructure you deploy and control. Not SaaS subscriptions, not a code library. Authentication, monitoring, databases, UIs—everything included. Azure AI-level completeness with LangChain-level ownership.
  - title: 30 minutes to production AI
    details: One command deploys everything. LLM gateway, vector search, chat interface, authentication, monitoring. Pre-built agents work immediately. No cloud provisioning, no complex setup, no infrastructure engineering.
  - title: One GPU, zero cloud dependency
    details: Run the entire platform—chat, embeddings, reranking, OCR, speech—on a single NVIDIA RTX 6000 Pro. No API keys, no egress traffic, no cloud bills. Full AI capability in an air-gapped rack. When cloud access is available, Swiss LLM Cloud scales you further without code changes.
  - title: Transparent, not black-box AI
    details: Every agent follows explicit workflows. Every decision is traceable and auditable. Every cost is tracked. See exactly why AI gave an answer. Trust through transparency, not promises. Built for Swiss standards.
  - title: Collective strength through collaboration
    details: Swiss organizations sharing infrastructure, competing on innovation. Contribute improvements, benefit from others'. Build together what no single organization could afford. The Swiss AI advantage.
---

<div style="height: 500px"></div>

## FAQ

::: details How can our Swiss organization deploy AI while keeping all data on-premise?
The Swiss AI Hub is an **open-source AI platform** that *you* deploy and control. It's specifically designed for
**on-premise installation** within your own Swiss data center. This means you can run the entire AI infrastructure -
including language model gateways and knowledge databases - on your servers, ensuring complete control and data
isolation. You can find more details in our
[Deployment Options](docs/2_platform/3_deployment_guide/1_deployment_options/).
:::

::: details How can we use AI and comply with Swiss data protection laws like FADP (revDSG)?
Ensuring **Swiss data sovereignty** is a core principle of the Swiss AI Hub community. Because *you* deploy the
platform, you choose *where* it runs – either on your own servers in Switzerland or within trusted Swiss data centers.
By using local Large Language Models (LLMs), sensitive data processing stays entirely within your control, helping you
meet **FADP (revDSG) requirements**. Read about our commitment in
[The Swiss Way: Privacy, Sovereignty, and Transparency](docs/1_vision_and_positioning/1_introduction/3_the_swiss_way/).
:::

::: details What is a trustworthy, open-source AI platform alternative to large cloud vendors like Azure AI or Google Vertex AI?
The Swiss AI Hub offers an **open-source alternative** built by a community focused on user control. The platform's core
infrastructure is licensed under Apache 2.0, meaning *you* own your deployment. This lets you avoid **vendor lock-in**,
giving you freedom from specific ecosystems and unpredictable pricing structures common with large cloud providers. See
how we compare in the [Comparison Matrix](docs/1_vision_and_positioning/2_why_swiss_ai_hub/1_comparison_matrix_light/).
:::

::: details How can we ensure AI decisions made within our Swiss company are traceable and auditable?
The Swiss AI Hub community prioritizes **transparency for trust**. Our platform provides deep observability features.
Every step an AI agent takes is visible, decisions are logged with context, and costs are tracked. Tools like Langfuse
allow tracing every interaction, so you can always understand *why* an AI provided a certain answer, which is crucial
for **compliance and auditing**. Explore these features under [Auditing & Observability](docs/2_platform/12_auditing/).
:::

::: details Is there a ready-made AI infrastructure stack (auth, monitoring, vector DBs) that we can deploy ourselves?
Yes, the Swiss AI Hub provides a **complete, pre-integrated AI infrastructure stack** that *you* deploy. It bundles
essential components like authentication, monitoring, various databases (including vector databases for AI), data
processing pipelines, and user interfaces right out of the box. This solves many common **production AI challenges**
from day one. Learn about this in
[The 'Day 2' Advantage](docs/1_vision_and_positioning/2_why_swiss_ai_hub/2_the_day_2_advantage/).
:::

::: details What is the quickest way to set up a secure, enterprise-ready AI platform within Switzerland?
You can deploy the entire Swiss AI Hub platform in about **30 minutes using a single command**. As an open-source
platform you install yourself, it includes pre-built agents and interfaces that start working immediately, offering
rapid time-to-value without complex cloud configurations. Get started with the
[Quick Start Guide](docs/2_platform/1_quick_start/).
:::

::: details How can our employees securely access company-specific AI help directly within Microsoft Teams or Slack?
The Swiss AI Hub platform includes **built-in integrations for Microsoft Teams and Slack**. This allows your employees
to interact securely with AI agents, which have access to relevant company knowledge, directly within the collaboration
tools they use every day, improving workflow. See details on
[Slack & Teams Integrations](docs/2_platform/17_slack_teams_integrations/).
:::

::: details How can our organization centrally manage access and usage of various AI models (e.g., GPT-4, Gemini, local models)?
The Swiss AI Hub includes an **integrated LLM Proxy (LiteLLM)** that acts as a unified gateway to all your configured AI
models. You can centrally manage model access, route requests based on policies, track costs across different providers,
and even set up failover mechanisms. More info is available under
[Language Models](docs/2_platform/13_language_models/).
:::

::: details How can we effectively control and predict the operational costs associated with using AI models?
Our community built the Swiss AI Hub with **transparent cost control** in mind. The integrated LLM Proxy tracks token
usage for every interaction, per user or agent. You can monitor AI spending in real-time dashboards and configure
budgets to prevent unexpected costs. Learn more about [Cost Control](docs/2_platform/14_cost_control/).
:::

::: details Our Swiss company has strict data privacy rules preventing the use of public AI clouds. What secure AI solution can we use?
The Swiss AI Hub is ideal for this. As an open-source platform *you* deploy, you can install it **fully on-premise** and
use **local, self-hosted LLMs**. This ensures that absolutely no data (prompts, responses, documents) ever leaves your
secure network perimeter. Review our comprehensive [Security features](docs/2_platform/20_security/).
:::

::: details We have AI prototypes using frameworks like LangChain but find deploying them reliably in production difficult. How can the Swiss AI Hub help?
The Swiss AI Hub provides the necessary **production-ready infrastructure** that development frameworks often lack.
While LangChain helps build the AI logic, our platform delivers the essential surrounding components: robust deployment
mechanisms, enterprise authentication, scaling, monitoring, and user interfaces needed for **reliable enterprise use**.
See [Our Solution](docs/1_vision_and_positioning/1_introduction/2_our_solution/).
:::

::: details How can we securely let AI agents answer questions based on our internal company documents (like PDFs or Word files)?
The Swiss AI Hub includes a secure **Retrieval-Augmented Generation (RAG) system**. You configure automated
[Data Pipelines](docs/2_platform/6_pipelines/) to ingest documents from your sources (like SharePoint). These pipelines
securely process the documents and index them in a vector database *that you own and control*, allowing agents to access
company knowledge safely.
:::

::: details Different teams in our organization are using various AI tools, creating silos. How can we create a unified, governed AI approach?
The Swiss AI Hub can serve as your **central, unified AI platform**. It provides common infrastructure that all teams
can build upon, ensures consistent governance and security policies, offers unified monitoring, and includes an
[OpenAI-Compatible API](docs/2_platform/18_api/1_openai_compatible_api/) allowing integration with many existing tools,
helping to **reduce fragmentation**.
:::

::: details What is an efficient and scalable way to handle the ingestion and vector embedding of thousands of company documents for AI?
The Swiss AI Hub utilizes **Data Pipelines**, built using the robust orchestrator Dagster. These pipelines automate the
entire workflow: connecting to your data sources, parsing various file formats intelligently, creating semantic chunks,
generating vector embeddings, and indexing them into your vector store (like Milvus). Find details in the
[Pipelines section](docs/2_platform/6_pipelines/).
:::

::: details Can we deploy and run a complete AI platform entirely offline in an air-gapped network within Switzerland?
Yes. When you deploy the Swiss AI Hub **on-premise** and configure it to use only **self-hosted Large Language Models**
(LLMs), the entire platform can operate without any external internet connection. This makes it suitable for
**air-gapped environments** with the highest security requirements. See
[Deployment Options](docs/2_platform/3_deployment_guide/1_deployment_options/).
:::

::: details How do we ensure the AI agents provide trustworthy answers and aren't just "hallucinating" or making things up?
Trust is paramount. Swiss AI Hub **Agents** are designed to follow explicit, defined workflows. They primarily use
**Retrieval-Augmented Generation (RAG)**, meaning their answers are based on information retrieved from *your* verified
company documents. Agents also **cite their sources**, and built-in "guardrails" check if the retrieved information is
sufficient, ensuring **reliable, fact-based responses**. Learn more about [Agents](docs/2_platform/5_agents/).
:::

::: details Is it possible for AI agents on this platform to ask for help or approval from human experts during complex tasks?
Yes, our platform supports **Human-in-the-Loop (HITL)** and **Bot-in-the-Loop (BITL)** workflows. An AI agent can be
designed to pause its process at a specific step, send a request for input or approval to a designated human expert (for
example, via a Slack message), and then seamlessly resume its work once the human responds. Explore
[Agent Fundamentals](docs/3_sdk/2_building_agents/1_agent_fundamentals/) which enable these patterns.
:::

::: details How does the Swiss AI Hub connect and integrate with our existing enterprise software like SharePoint or internal databases?
The platform offers **flexible integration options**. AI agents can make direct API calls to external systems; external
systems can trigger agents via the platform's [Agent Interaction API](docs/2_platform/18_api/2_agent_interaction_api/);
automated Data Pipelines can sync knowledge from sources like SharePoint; and standard protocols are supported for
custom connections. See [External Integrations](docs/2_platform/22_external_integrations/).
:::

::: details How does using an open-source platform like Swiss AI Hub benefit the broader Swiss AI community?
Our **ecosystem model** is built on collaboration. The core platform is open-source, allowing Swiss organizations to
pool efforts in building and improving the fundamental AI infrastructure. Everyone benefits from shared advancements,
letting individual organizations focus resources on creating unique AI applications specific to their needs,
strengthening Switzerland's overall AI capabilities. Read about
[The Ecosystem Model](docs/1_vision_and_positioning/2_why_swiss_ai_hub/3_the_ecosystem_model/).
:::

::: details We are concerned about the complexity of setting up and managing a self-hosted AI platform. Is the Swiss AI Hub difficult to operate?
The Swiss AI Hub community designed the platform for **simplified deployment and management**. The installation uses a
single command, and critical infrastructure challenges like authentication, monitoring, and scaling configuration are
solved out-of-the-box. This significantly reduces the operational complexity compared to building AI infrastructure from
scratch or managing intricate cloud vendor services. Check the [Quick Start](docs/2_platform/1_quick_start/).
:::
