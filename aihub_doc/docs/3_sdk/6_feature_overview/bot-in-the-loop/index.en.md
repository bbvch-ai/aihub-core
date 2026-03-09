---
title: Bot-in-the-Loop
---

# Bot-in-the-Loop :left_right_arrow: :100:

::: info **TL;DR - What is Bot-in-the-Loop?**
Bot-in-the-Loop enables AI agents to **seamlessly pause workflows and request human input via Slack channels**, then
automatically continue execution with the human response. This pattern bridges the gap between autonomous AI processing
and human expertise, allowing agents to handle complex decisions while maintaining full automation around human
involvement.
:::

## What is Bot-in-the-Loop and How Does It Work? :brain:

Bot-in-the-Loop represents a sophisticated **human-AI collaboration pattern** that enables AI agents to pause their
automated workflows at critical decision points and seamlessly integrate human expertise through structured Slack
interactions.

**Workflow Integration Architecture** allows AI agents to invoke Bot-in-the-Loop at any point in their execution. When
an agent encounters a decision requiring human input, approval, or expertise, it emits a `BotInTheLoopRequestEvent` that
automatically:

- Posts a formatted question to a designated Slack channel
- Maintains full workflow context and conversation threading
- Waits for human response without blocking other system operations
- Captures the response and automatically resumes agent execution

**Slack Channel Integration** provides the human interface through familiar collaboration tools. Experts respond
directly in Slack threads, where:

- Questions appear as structured, threaded messages
- Multiple experts can collaborate on responses
- Response attribution tracks who provided input
- Conversation history is maintained for audit and learning

**Event-Driven Orchestration** powers the entire interaction through the AI-Hub's event system:

- `BotInTheLoopRequestEvent` pauses workflows and posts to Slack
- `BotInTheLoopResponseEvent` captures responses and resumes workflows
- Full context preservation ensures seamless continuation
- Error handling manages timeouts and failed responses

**Agent Workflow Integration** uses the simple `BotInTheLoop.invoke()` helper that makes integration trivial for agent
developers:

```python
# Pause workflow for human input
return BotInTheLoop.invoke(
    user=current_user,
    question="Should I proceed with this high-risk operation?",
    slack_channel_id="C08MCK6LEBY"
)
```

**Key Technologies:**

- **NATS Event System** - Asynchronous message routing and workflow orchestration
- **Slack Bot Framework** - Channel integration with threading and attribution
- **Azure Bot Service** - Multi-channel bot connectivity and message processing
- **Event Store** - Persistent context and conversation tracking
- **Agent Workflow Engine** - Seamless integration with AI agent execution flows

## Why This is a Game-Changer for Your AI Strategy :trophy:

Bot-in-the-Loop transforms how organizations approach AI automation by solving the critical challenge of human-AI
collaboration at scale:

**🤝 Seamless Human-AI Collaboration**: AI agents can now naturally involve human experts without breaking automated
workflows. Complex decisions, approvals, and knowledge validation happen through familiar Slack interactions, while the
AI maintains full context and automatically continues processing with human input.

**⚡ Uninterrupted Automation**: Unlike traditional systems that require manual intervention points, Bot-in-the-Loop
maintains continuous automation around human involvement. Agents pause only when necessary, request specific input, and
immediately resume processing, maximizing both efficiency and human expertise utilization.

**🧠 Scalable Expert Knowledge Integration**: Subject matter experts can efficiently support multiple AI workflows
simultaneously through structured Slack interactions. One expert consultation can inform multiple agents, and their
knowledge is captured for organizational learning and future automation improvements.

**🛡️ Risk-Aware Decision Making**: Critical decisions that require human judgment - regulatory compliance, high-stakes
approvals, or complex interpretations - can be seamlessly integrated into otherwise automated processes. This ensures
both speed and safety in AI-powered workflows.

**📚 Organizational Knowledge Capture**: Every human response is captured with full context, creating an ever-growing
repository of expert decisions and knowledge. This enables continuous improvement of AI systems and builds institutional
knowledge that survives personnel changes.

::: details **Setting Up and Using Bot-in-the-Loop**
## Configuration Requirements

### Slack Bot Setup

1. **Azure Bot Service Configuration**: Ensure your AI-Hub has Azure Bot Service integration configured

   ```bash
   python aihub_bot/setup_azure_bot.py \
     --resource-group "your-resource-group" \
     --bot-name "your-ai-hub-bot" \
     --token-url "https://your-aihub-domain.com" \
     --slack-token "xoxb-your-slack-oauth-token"
   ```

2. **Slack App Configuration**: Create a Slack App with required permissions

   - **Bot Token Scopes**: `channels:read`, `chat:write`, `chat:write.public`, `users:read`
   - **Event Subscriptions**: Subscribe to `message.channels` events
   - **OAuth Installation**: Install the app to your workspace

3. **Channel Access**: Ensure your bot is added to the Slack channels where you want to post questions

   ```
   /invite @YourAIHubBot
   ```

### Agent Integration Setup

1. **Import Bot-in-the-Loop Helper**: Add to your agent imports

   ```python
   from aihub_lib.nats.events.bot_in_the_loop import BotInTheLoop
   ```

2. **Configure Slack Channel IDs**: Identify your Slack channel IDs (format: `C08MCK6LEBY`)

   ```python
   # Right-click channel → View channel details → Copy channel ID
   EXPERT_CHANNEL_ID = "C08MCK6LEBY"
   ```

3. **NATS Event Distribution**: Ensure your AI-Hub deployment has NATS messaging configured for event routing

## Usage Examples

### Basic Agent Integration

**Simple Decision Point:**

```python
class ApprovalAgent(Agent):
    @step()
    async def approval_step(
        self, 
        event: RequestEvent, 
        run_context: RunContext
    ) -> BotInTheLoop.request:
        user = await run_context.get("user")
        return BotInTheLoop.invoke(
            user=user,
            question=f"Approve budget request for ${event.amount}?",
            slack_channel_id="C08MCK6LEBY"
        )
    
    @step()
    async def process_approval(
        self, 
        response: BotInTheLoop.response
    ) -> ApprovedEvent | RejectedEvent:
        if response.response.lower() in ["yes", "approved", "approve"]:
            return ApprovedEvent(approver=response.responder.user_name)
        return RejectedEvent(reason=response.response)
```

### Expert Consultation Workflow

**Knowledge-Seeking Pattern:**

```python
class ExpertConsultationAgent(Agent):
    @step()
    async def consult_expert(
        self, 
        event: ComplexQuestionEvent, 
        agent_config: ConsultationConfig
    ) -> BotInTheLoop.request:
        return BotInTheLoop.invoke(
            user=event.user,
            question=f"Expert input needed: {event.question}",
            slack_channel_id=agent_config.expert_channel_id
        )
    
    @step()
    async def process_expert_response(
        self, 
        response: BotInTheLoop.response,
        agent_config: ConsultationConfig
    ) -> ExpertAnswerEvent:
        # Optionally save to knowledge base
        if agent_config.save_to_knowledge_base:
            await self.save_expert_knowledge(
                question=response.request_event.question,
                answer=response.response,
                expert=response.responder.user_name
            )
        
        return ExpertAnswerEvent(
            answer=response.response,
            expert_name=response.responder.user_name,
            confidence_score=self.assess_response_quality(response.response)
        )
```

### Multi-Stage Approval Process

**Sequential Human Checkpoints:**

```python
class MultiStageApprovalAgent(Agent):
    @step()
    async def technical_review(
        self, 
        event: SubmissionEvent
    ) -> BotInTheLoop.request:
        return BotInTheLoop.invoke(
            user=event.user,
            question=f"Technical review: {event.proposal_summary}",
            slack_channel_id="C08TECH123"  # Technical team channel
        )
    
    @step()
    async def business_approval(
        self, 
        technical_response: BotInTheLoop.response
    ) -> BotInTheLoop.request:
        return BotInTheLoop.invoke(
            user=technical_response.request_event.user,
            question=f"Business approval needed. Technical review: {technical_response.response}",
            slack_channel_id="C08BIZ456"  # Business team channel
        )
    
    @step()
    async def final_decision(
        self, 
        business_response: BotInTheLoop.response
    ) -> FinalDecisionEvent:
        return FinalDecisionEvent(
            approved=self.parse_approval(business_response.response),
            technical_reviewer=business_response.request_event.request_event.responder.user_name,
            business_approver=business_response.responder.user_name
        )
```

## Available Capabilities

**Agent Workflow Integration:**

- **Simple Invocation**: One-line integration with `BotInTheLoop.invoke()`
- **Context Preservation**: Full workflow state maintained across human interactions
- **Response Processing**: Structured response handling with user attribution
- **Error Handling**: Timeout management and graceful failure handling

**Slack Channel Features:**

- **Threaded Conversations**: Responses are captured in organized threads
- **Multi-Expert Support**: Multiple experts can collaborate on responses
- **User Attribution**: Track who provided each response for accountability
- **Rich Formatting**: Support for Slack markdown and structured messages

**Event System Integration:**

- **Asynchronous Processing**: Non-blocking human interactions with parallel workflow support
- **Event Persistence**: Full conversation history stored for audit and replay
- **Cross-Agent Communication**: Responses can be shared between different agent workflows
- **Monitoring Integration**: Langfuse tracing and observability for human interaction patterns

## Security and Best Practices

**Security Considerations:**

- **Channel Access Control**: Restrict bot access to designated expert channels only
- **User Authentication**: Slack user identity is captured and attributed to responses
- **Audit Trails**: Complete conversation history maintained for compliance requirements
- **Sensitive Data Handling**: Questions should avoid exposing confidential information in channel messages

**Best Practices:**

- **Channel Organization**: Create dedicated channels for different types of expert consultation (technical, legal,
  business)
- **Question Formatting**: Structure questions clearly with context and specific asks to get quality responses
- **Response Validation**: Implement basic validation of human responses before continuing workflows
- **Timeout Management**: Set appropriate expectations for response times and handle timeouts gracefully
- **Knowledge Capture**: Consider automatically saving valuable expert responses to knowledge bases

**Performance Optimization:**

- **Channel Distribution**: Distribute different question types across multiple channels to prevent expert overload
- **Batching**: For similar questions, consider batching requests to reduce expert interruption
- **Caching**: Cache common expert responses to reduce redundant questions
- **Escalation Paths**: Implement escalation when primary experts are unavailable
:::

## Getting Started

To implement Bot-in-the-Loop in your AI-Hub deployment:

1. **Configure Slack Integration**: Set up Azure Bot Service with Slack connectivity and ensure your bot has access to
   designated expert channels
2. **Identify Expert Channels**: Create or identify Slack channels where subject matter experts are available to respond
   to agent questions
3. **Integrate in Agent Workflows**: Use the simple `BotInTheLoop.invoke()` pattern at decision points where human input
   adds value to automated processes

For detailed agent integration patterns, see the
[Expert Agents documentation](../../../2_platform/5_agents/3_expert_asking_agent/) for real-world implementation
examples, and the AI-Hub Agent Developer's Guide for comprehensive workflow integration instructions.
