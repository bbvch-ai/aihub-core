---
title: Vision
index: 1
---

# Vision of the Swiss AI-Hub :rocket:

## 🎯 Not just a tool—your AI platform

The Swiss AI-Hub is a 100% open-source enterprise AI platform that you own, extend, and build upon. Apache 2.0 licensed
with zero vendor lock-in, it provides an alternative to proprietary AI platforms while maintaining Swiss data
sovereignty.

::: danger Core philosophy
It's not our platform. It's YOUR platform. Deploy it, modify it, extend it. Build your competitive advantage on top of
it.
:::

## 🏗️ Platform + SDK: The complete ecosystem

### The platform (Swiss AI-Hub)

Your central AI infrastructure—Apache 2.0 licensed and open. It handles secure LLM access, data pipelines,
orchestration, and integrations. Think of it as your AI operating system.

### The SDK (Swiss AI-Hub SDK)

Tools and interfaces to transform your business logic into robust AI agents that run on the platform. It includes
documentation, developer tools, and an AI assistant that helps you build AI assistants.

::: tip Build once, deploy everywhere
Agents built with the SDK integrate seamlessly into the platform, inheriting its security, observability, and
scalability.
:::

## 🧠 Your AI journey: evolve at your pace

The platform grows with you through three tiers:

### 🔐 Tier 1: Secure LLM – your foundation

A secure, controllable gateway to AI that you can build upon. Access any LLM—open-source or commercial—through your
unified interface. Run Mistral or DeepSeek entirely on-premise so your data never leaves your infrastructure.

![Swiss AI-Hub Architecture](../../../media/tier1.png)

:::details The platform advantage
You get the entire infrastructure, not just "LLM access as a service." Fork it, modify it, add your own models. The
Admin UI is your control center for extending the platform itself.
:::

### 🤖 Tier 2: Assistant – your custom experts

Transform the platform into your specialized workforce. Your developers use the SDK to build assistants that understand
your business context, integrate with your data, and follow your rules. You're not limited to pre-built
assistants—create exactly what you need.

:::details SDK in action: building your finance assistant
```javascript
// Using the Swiss AI-Hub SDK
const financeAssistant = createAssistant({
  name: "Finance-Expert",
  knowledge: ["erp-data", "contracts", "forecasts"],
  capabilities: ["analyze", "forecast", "audit"],
  guardrails: companyPolicies.finance
});

// Deploy directly to your hub
hub.deploy(financeAssistant);
```

Your assistant immediately becomes available across Teams, Slack, and the web UI.
:::

![Swiss AI-Hub Architecture](../../../media/tier3.png)

### 🌟 Tier 3: Agentic process automation – your orchestrated enterprise

The platform becomes your business process orchestrator. Agents built with the SDK coordinate workflows between humans,
AI, and existing systems. The hub doesn't replace your tools—it orchestrates them. Power Automate, n8n, SAP, and
Salesforce all connect through the platform.

::: danger Human control by design
Agents operate within strict guardrails with clear escalation points. Every action is logged, every decision traceable,
and humans can intervene at any moment.
:::

:::details Example: intelligent HR process
1. Application arrives → Existing tool extracts data
2. Document Analysis Agent → Reviews CV for qualifications
3. Matching Agent → Scores candidate against open positions
4. **Human HR Manager** → Makes hiring decision
5. Communication Agent → Drafts personalized response
6. **Human** → Approves communication
7. Automation tool → Sends final email

The process runs 10x faster while humans retain strategic decisions.
:::

![Swiss AI-Hub Architecture](../../../media/tier4.png)

## 🚀 Why "your platform" matters

Traditional vendors make you adapt to their platform, accept their limitations, and pay their fees forever. The Swiss
AI-Hub adapts to you. You extend it with your logic, integrate it with your systems, and build your competitive
advantage on top of it.

### For your business

- **No lock-in**: Apache 2.0 lets you take it anywhere
- **Full control**: Every component is transparent and modifiable
- **Swiss sovereignty**: Your data, your rules, your compliance

### For your developers

- **SDK power**: Build agents that become platform-native
- **Open ecosystem**: Contribute back, benefit from community innovations
- **Real ownership**: Actual infrastructure control, not just API access

### For your future

- **Investment protection**: Build on a foundation you own
- **Competitive advantage**: Your custom agents are yours alone
- **Ecosystem growth**: Join a community building the open AI future

## 🌍 The open AI revolution

The Swiss AI-Hub is infrastructure you own, extend, and build upon. An SDK that turns your ideas into production agents.
An ecosystem that grows with your ambitions.

Start with secure experimentation. Build custom assistants. Orchestrate intelligent processes. All on YOUR platform.
