---
title: Expert asking agent
index: 3
---

# Expert asking agent

When a RAG agent cannot answer a question from its knowledge base, it can escalate the query to human experts. The
expert agents implement this escalation workflow through two specialized agents that work together.

## Agent pair architecture

The system uses two agents:

The Expert Grounded Agent interacts with users. It searches its knowledge base for answers. When information is
insufficient, it informs the user and asks permission to escalate the question to a human expert.

The Expert Asking Agent manages the consultation process. It posts questions to experts via Slack, captures their
responses, and stores the answers in the knowledge base for future queries.

## Workflow

```mermaid
sequenceDiagram
    participant User
    participant GroundedAgent as Expert Grounded Agent
    participant KnowledgeBase as Knowledge Base
    participant AskingAgent as Expert Asking Agent
    participant Slack
    participant HumanExpert as Human Expert

    User->>+GroundedAgent: Asks a complex question
    GroundedAgent->>+KnowledgeBase: Searches for relevant context
    KnowledgeBase-->>-GroundedAgent: Returns insufficient/no context
    
    GroundedAgent-->>User: "I don't know. May I ask an expert?"
    User->>+GroundedAgent: "Yes, please."
    
    GroundedAgent->>+AskingAgent: Delegates question (Agent-in-the-Loop)
    Note right of AskingAgent: Manages the human interaction
    
    AskingAgent->>+Slack: Posts question to expert channel
    Slack->>+HumanExpert: Notifies expert of the question
    
    HumanExpert->>+Slack: Provides answer in thread
    Slack-->>-AskingAgent: Forwards expert's response
    
    Note over AskingAgent: Evaluates response for completeness.<br/>(Optional: Asks follow-up questions if needed)

    AskingAgent->>+KnowledgeBase: Saves expert's answer as a new<br/>knowledge snippet for future use
    KnowledgeBase-->>-AskingAgent: Confirms knowledge is stored
    
    AskingAgent-->>-GroundedAgent: Returns the final, verified answer
    GroundedAgent-->>-User: Delivers the expert's answer
```

The sequence diagram shows the complete consultation workflow.

The user asks the Expert Grounded Agent a question. The agent searches the knowledge base. If the search returns
insufficient information, the agent informs the user and requests permission to consult an expert.

With user consent, the Grounded Agent delegates to the Expert Asking Agent using the agent-in-the-loop pattern. The
Asking Agent posts the question to a configured Slack channel, notifying the designated expert.

The expert provides an answer in the Slack thread. The Asking Agent can evaluate response completeness and ask follow-up
questions if needed. Once satisfied, it stores the answer in the knowledge base and returns the response to the Grounded
Agent, which delivers it to the user.

Future queries on the same topic retrieve the stored expert answer from the knowledge base without requiring another
consultation.

## Knowledge capture

Each expert consultation adds to the knowledge base. Experts answer questions once, and their responses become
searchable for all users. This converts tacit knowledge into documented information without requiring experts to use
additional tools beyond their existing Slack workspace.

The Asking Agent can detect incomplete responses and generate follow-up questions to ensure captured knowledge is
comprehensive enough for future retrieval.
