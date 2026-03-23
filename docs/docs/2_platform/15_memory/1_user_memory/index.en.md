---
title: User Memory
---

# User memory

User memory enables AI agents to learn your personal preferences, working style, and individual context. This memory is
private to you - no other user can see what agents have learned about your preferences. Over time, agents adapt their
behavior to match how you work.

## What gets remembered

Agents automatically learn information that helps them serve you better. This includes your preferred programming
languages, communication style, level of detail in responses, and format preferences. If you consistently ask for
concise answers, agents learn to be brief. If you prefer detailed explanations with examples, they adapt accordingly.

Agents also learn your technology stack, current projects, typical tasks, and areas of expertise. When you frequently
discuss Python development, agents recognize this and frame technical suggestions in Python terms. Process patterns like
how you prefer to handle approvals, your typical working hours, and workflow habits get captured too.

User memories are strictly isolated to your account. When an agent learns that you prefer detailed code comments, that
preference affects only your interactions. Other users might prefer minimal comments, and their agents adapt
differently. This isolation extends across agent types - each agent learns preferences relevant to its function without
interfering with others.

## How it works

User memory requires no manual effort. As you converse with agents, they analyze the conversation to identify useful
information worth remembering. After processing your conversation, the agent asks itself: "What did I learn about this
user's preferences or context that would help me serve them better in the future?"

This approach means you don't maintain preference lists or fill out profile forms. Agents learn from how you actually
work, not how you think you work. As your preferences evolve, new memories reflect those changes.

Different agent types focus on different aspects. Code assistants learn your preferred languages, frameworks, coding
style, and the types of examples you find helpful. Knowledge retrieval agents learn which topics interest you, your
preferred information depth, and how you like sources cited. Process orchestration agents learn your approval
thresholds, notification preferences, and how you interact with automated workflows.

Agents maintain awareness of when memories were created. If you mentioned working on "the new dashboard project" six
months ago and mention it again today, the agent understands these might be different projects or different phases of
the same project.

## Viewing your memories

Access the **User Memory** service through the platform's navigation to see everything agents have learned about you.
Each memory displays the actual information remembered (e.g., "User prefers Python over JavaScript for backend
development"), when this memory was learned, which agent identified this preference, and the thread where this
information originated. You can click through to the source conversation to see the exact context that generated the
memory.

The interface supports semantic search. Instead of exact keyword matching, you can search by meaning. Searching for
"programming languages" will find memories about your Python preference, JavaScript experience, and TypeScript
interests, even if those exact words don't appear in your search.

Some memories connect to others through relationships. If agents learn you "work on Project Falcon" and "Project Falcon
uses microservices," the interface can show these connections as a graph, helping you understand how agents connect
different pieces of information about your context.

## Managing your memories

Click any memory to edit its content. This is useful when an agent learned something slightly incorrect, your
preferences have changed, or you want to refine how something is expressed. Editing a memory immediately affects how
agents use that information - if you correct "User prefers brief responses" to "User prefers detailed explanations with
examples," agents adapt their behavior in the next conversation.

You can delete individual memories that are no longer relevant or accurate, or delete all your user memories at once.
Common reasons include role changes that make old technical preferences irrelevant, completed projects whose context no
longer applies, privacy concerns about specific information, or wanting agents to relearn your preferences from scratch.
Deletion is immediate and irreversible.

::: info GDPR compliance
The platform fully supports your data protection rights: access (view all memories), rectification (edit any memory),
erasure (delete specific or all memories), and data portability (export via API). Deleting all user memories satisfies
your right to be forgotten regarding preference data.
:::

## Practical examples

### Code assistant adaptation

In week one, you ask a code assistant for help with a Python function. The agent creates a memory: "User works with
Python." The following week, you ask about authentication. Without being told, the agent provides Python examples rather
than other languages. It also notices you appreciate inline comments and creates another memory about your documentation
preferences. By week four, when you ask about a complex algorithm, the agent automatically provides Python code with
detailed comments, having learned both preferences from your actual behavior.

### Knowledge retrieval personalization

You ask a knowledge agent about machine learning and receive a comprehensive overview. The agent notes your interest.
When you ask for more details on a specific aspect, it provides technical depth and remembers that you prefer detailed
technical explanations over high-level summaries. In later interactions about different topics, the agent automatically
provides similar depth and proactively mentions connections to machine learning.

### Process agent learning

A process agent asks you to approve a document. You approve with comments about formatting, and the agent learns you
check formatting before approval. In subsequent requests, it includes formatting verification in its pre-approval
checklist. Over time, it also learns when you prefer to receive approval requests based on your response patterns.

## Memory evolution

User memories are not static. Early memories might be broad: "User works with web development." Later memories refine
this: "User specializes in frontend development using Vue.js and TypeScript." Agents don't delete the earlier memory -
both remain. The more specific memory takes precedence when relevant, while the broader memory applies in general
contexts.

If you explicitly contradict an earlier preference, agents can recognize this. If they learned "User prefers brief
responses" but you ask for more detail, they'll create a new memory reflecting the change. The platform preserves both
memories with timestamps, allowing agents to understand your preferences have evolved rather than treating the
contradiction as an error.

Agents develop stronger confidence in preferences they observe repeatedly. A one-time interaction creates a tentative
memory; consistent behavior reinforces that memory's importance.

## Best practices

Don't try to "program" agents by making artificial statements about your preferences. Work naturally, and agents will
learn from your actual behavior. This produces more accurate memories than trying to dictate preferences upfront.

Check your user memories occasionally to see what agents have learned. This helps you catch incorrect inferences early,
understand why agents behave certain ways, and decide if you want to adjust any learned preferences. If an agent learned
something incorrect, edit the memory directly rather than trying to correct it through conversation - direct editing is
faster and more reliable.

User memory is designed to work in the background. You don't need to think about it constantly. The transparency
features exist for verification and control, not because you need to actively manage the system.

::: details How memory affects performance
User memories are retrieved at the start of each conversation with an agent. The retrieval adds minimal latency –
typically under 100ms. Semantic search ensures only relevant memories are included in the agent's context.
:::

::: details Memory limits
The system doesn't impose hard limits on user memory count. Agents focus on the most relevant memories for each
conversation. Having thousands of memories doesn't slow down interactions because only pertinent information is
retrieved.
:::

::: details Cross-agent memory sharing
While each agent type specializes in what it learns, factual memories (not preferences) can be shared across agents. If
one agent learns "User is working on Project Falcon," other agents can access that factual context. Preferences like
"User prefers concise responses" remain agent-specific.
:::
