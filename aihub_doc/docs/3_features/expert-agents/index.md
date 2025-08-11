---
title: "Expert Agents"
index: 2
---

# Expert Agents :bust_in_silhouette: :100:

::: info **TL;DR - What are Expert Agents?**
Expert Agents bridge the gap between AI knowledge and human expertise by **automatically connecting users to subject matter experts** when the AI lacks sufficient information. These agents ensure responses are always grounded in reliable knowledge and seamlessly escalate to human experts through Slack channels, capturing their responses for organizational learning.
:::

## What are Expert Agents and How Do They Work? :brain:

Expert Agents represent a breakthrough in **human-AI collaboration**, implementing two specialized agents that work together to ensure users always receive accurate, well-grounded responses:

**Expert Grounded Agent** acts as the primary user interface, ensuring all responses are based on verified context. When it encounters questions that cannot be answered with available information, it asks for user consent and seamlessly escalates to human experts.

**Expert Asking Agent** manages the expert consultation process, posting questions to designated Slack channels, engaging with experts through iterative questioning, and automatically capturing expert knowledge for future use.

The system integrates with **Slack channels** where subject matter experts naturally work, **OpenWebUI knowledge bases** for persistent learning, and the **[Bot-in-the-Loop infrastructure](../bot-in-the-loop/)** that enables seamless human participation in AI workflows.

**Key Technologies:**
- **Agent-in-the-Loop Pattern** - Orchestration between specialized agents
- **[Bot-in-the-Loop Integration](../bot-in-the-loop/)** - Direct Slack channel interaction for human expertise
- **Context Validation** - LLM-powered assessment of information sufficiency
- **Knowledge Persistence** - Automatic storage in OpenWebUI knowledge bases
- **Multi-language Support** - Full internationalization across German, English, French, and Italian

## Why This is a Game-Changer for Your AI Strategy :trophy:

Expert Agents solve the critical challenge of **AI knowledge limitations** while building organizational intelligence:

**🛡️ Guaranteed Accuracy**: Expert Grounded Agents refuse to hallucinate or guess, ensuring responses are always based on verified information. When knowledge is insufficient, they escalate to human experts rather than providing potentially incorrect answers.

**🔄 Seamless Expert Integration**: Subject matter experts contribute knowledge without leaving their familiar Slack environment. The system captures their expertise through natural conversation and automatically stores it for future reference.

**📚 Organizational Learning**: Every expert consultation becomes part of your organization's growing knowledge base. Expert responses are automatically processed, structured, and stored in OpenWebUI, creating a continuously expanding repository of verified knowledge.

**⚡ Efficient Knowledge Transfer**: The iterative questioning system ensures experts provide complete, actionable answers. If initial responses are insufficient, the system automatically generates follow-up questions until comprehensive knowledge is captured.

**🌐 Scalable Expertise**: Human experts can efficiently serve multiple AI-powered workflows through structured consultation processes. Their knowledge is captured once and benefits all future similar queries, multiplying their impact across the organization.

::: details **Setting Up and Using Expert Agents**

## Configuration Requirements

### Expert Grounded Agent Setup

1. **LLM Configuration**: Configure Azure OpenAI, Gemini, or OpenAI-compatible LLM
   ```yaml
   llm:
     name: "gpt-4o"
     base_url: "https://your-openai-endpoint.com"
     api_version: "2024-12-01-preview"
   ```

2. **Expert Asking Agent Reference**: Connect to your Expert Asking Agent instance
   ```yaml
   expert_asking_agent_class: "ExpertAskingAgent"
   expert_asking_agent_id: "your_expert_agent_id"
   ```

### Expert Asking Agent Setup

1. **Slack Integration**: Configure the Slack channel where experts will be consulted
   ```yaml
   slack_channel_id: "C08MK7Z8GU9"  # Your expert Slack channel ID
   ```

2. **OpenWebUI Knowledge Base**: Set up knowledge storage integration
   ```yaml
   open_webui_knowledge_id: "your-knowledge-base-id"
   open_webui_api_key: "your-api-key"
   open_webui_api_url: "http://localhost:8080"
   ```

3. **Loop Protection**: Configure maximum follow-up questions
   ```yaml
   loop_max: 3  # Maximum expert consultation rounds
   ```

## Usage Examples

### Basic Expert Consultation Flow

1. **User Question**: "What is our company's policy on remote work flexibility?"
2. **Context Assessment**: Agent evaluates available documentation
3. **Expert Escalation**: If policy details are insufficient, agent asks: "I lack the necessary knowledge to answer this question. Would you like me to obtain the required knowledge from an expert?"
4. **Slack Consultation**: Question posted to HR experts channel
5. **Response Capture**: Expert responds with detailed policy information
6. **Knowledge Storage**: Response automatically saved to knowledge base
7. **User Response**: Complete policy information delivered to user

### Iterative Expert Questioning

If expert's initial response lacks detail:
1. **Sufficiency Assessment**: LLM evaluates response completeness
2. **Follow-up Generation**: Automatic creation of clarifying questions
3. **Continued Engagement**: Expert provides additional details
4. **Knowledge Synthesis**: Final comprehensive response creation

## Available Capabilities

**Expert Grounded Agent Capabilities:**
- **Context Validation**: Automatic assessment of information sufficiency
- **User Consent Management**: Respectful escalation with user permission
- **Response Grounding**: Ensures all answers are based on verified sources
- **Graceful Degradation**: Handles expert unavailability professionally

**Expert Asking Agent Capabilities:**
- **Slack Integration**: Direct posting to expert channels with threading
- **Iterative Questioning**: Automatic follow-up until complete answers obtained
- **Knowledge Capture**: Structured storage of expert responses
- **Multi-round Conversations**: Support for complex consultations

## Security and Best Practices

**Security Considerations:**
- **Controlled Access**: Expert agents only access configured Slack channels
- **User Consent**: Always requests permission before contacting experts
- **Read-only Knowledge Storage**: Captured knowledge stored securely
- **Audit Trail**: Complete conversation history maintained

**Best Practices:**
- **Expert Channel Management**: Designate specific channels for different expertise areas
- **Response Time Expectations**: Set appropriate expert availability expectations
- **Knowledge Base Organization**: Structure OpenWebUI knowledge bases by domain
- **Regular Review**: Periodically review captured expert knowledge for accuracy

:::

## Getting Started

To implement Expert Agents in your AI-Hub deployment:

1. **Configure Slack Integration**: Set up dedicated expert consultation channels and ensure [Bot-in-the-Loop infrastructure](../bot-in-the-loop/) is running
2. **Deploy Expert Asking Agents**: Configure one or more Expert Asking Agents for different domains (HR, Legal, Technical, etc.)
3. **Implement Expert Grounded Agents**: Deploy grounded agents that connect to your Expert Asking Agents for seamless escalation

For detailed setup instructions, configuration examples, and troubleshooting guidance, refer to the AI-Hub Agent Developer's Guide and [Bot-in-the-Loop documentation](../bot-in-the-loop/) for integration details.