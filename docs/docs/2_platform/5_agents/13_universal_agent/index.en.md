---
title: Universal Agent
description: One assistant that decides for itself whether to search your knowledge, read attached files or recall memory, and keeps going until it can answer.
---

# Universal Agent

The **Universal Agent** works the way people expect a modern assistant to work. Instead of following a fixed sequence of
steps, it looks at each message and decides for itself what it needs: search your company's knowledge, read a file the
user attached, recall what it remembers about the user, or answer straight away. It keeps going, one tool after another,
until it can answer.

Every other agent on the platform follows a fixed workflow, so an admin picks the right one per use case and users have
to know which assistant to ask. A Universal Agent profile is configured once with the knowledge it may search, and users
ask it anything.

::: tip When to reach for this agent
Use the Universal Agent as a general assistant that combines your knowledge, the user's attachments and memory in one
conversation. When a use case needs a guaranteed, auditable sequence of steps — always retrieving from the same
collections, checking grounding before answering, escalating to an expert — use the dedicated blueprints such as the
[Document Intelligence Assistant](../5_document_intelligence_assistant/). They stay the predictable option.
:::

## What it does

```mermaid
flowchart LR
    A[User message] --> B[Prepare the<br/>conversation]
    B --> C{Model decides}
    C -->|needs a tool| D[Run the tool]
    D --> C
    C -->|can answer| E[Stream the answer]
```

1. **Prepare the conversation.** The agent's built-in instructions on using its tools, then your profile's own
   instructions, are put at the front of the conversation, and the history is trimmed to the input budget.
2. **Decide and use tools.** The model chooses which tools to call, the platform runs them and hands the results back,
   and the model decides again. It can call several independent tools in one round.
3. **Answer.** When the model has what it needs, its reply streams to the user with citations to the documents it used.

Nothing is loaded into the prompt in advance: a question that needs no lookup is answered directly, and one that needs
three lookups gets three.

### The tools

| Tool                      | What it does                                                                                                                                                                                                                                                                                                                                                        | Offered when                                                                 |
| ------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| **Search our knowledge**  | Searches the knowledge collections the profile allows, reranks the results and returns the best sections with ids to cite. The user's own `#` references are offered too. Only collections the asking user may read are ever searched.                                                                                                                              | The profile lists collections, or allows every collection the user can read. |
| **Read attached files**   | Reads the files attached to the conversation. The model sees which files are attached and reads the ones it needs; a file too long to read whole returns the sections most relevant to what the model is looking for.                                                                                                                                               | The user attached a document (images reach the model directly).              |
| **Recall memory**         | Searches what is remembered about the user and the organisation: preferences, facts and decisions from earlier conversations.                                                                                                                                                                                                                                       | User or organisation memory is enabled on the profile.                       |
| **Code sandbox**          | Runs commands and reads and writes files in the user's own code sandbox, in a folder per conversation that holds the conversation's attached files. A file the agent shows the user, such as a chart or a spreadsheet, is attached to the answer and stays downloadable.                                                                                            | The user switched on **Code Interpreter** in the chat.                       |
| **My files**              | Lists and reads the user's own files in [My Files](../../10_chat_ui/14_my_files/): their uploads, chat attachments and files agents made for them. Read-only.                                                                                                                                                                                                       | The user switched on **My Files** in the chat.                               |
| **Read linked web pages** | Reads the web pages the user linked in the message or attached with `#`, and only those: a call naming any other address is refused, so an instruction hidden in a page or file cannot send the conversation elsewhere. See [Linked web pages](../../10_chat_ui/15_linked_web_pages/).                                                                              | **Read Linked Web Pages** is on in the profile and the message links a page. |
| **Knowledge documents**   | Lists the documents of the knowledge collections by path, finds every document whose text contains an exact term or pattern, and reads a whole document a part at a time. Unlike the knowledge search, it finds every match, not the most similar passages. It never leaves the profile's collections or its document path filter.                                  | **Work on Whole Documents** is on in the profile.                            |
| **Extract a table**       | Collects records from many documents into one table, each row naming its file, as the [Knowledge Extraction Agent](../14_knowledge_extraction_agent/) does. The model first checks which documents a selection covers; the user sees the table directly, with its summary, and the model describes it. Asks the user's approval before every extraction by default. | **Work on Whole Documents** is on in the profile.                            |

More tools follow as the platform adds them: web search and image generation each add their tool to this agent.

Every tool call shows in the chat: the knowledge search and the files appear as sources, each call as a collapsible
block with what the tool returned, and the agent trace records each step.

### Staying within the model's context

Long conversations with many tool results can outgrow what the model can read. Before each decision, the agent checks
the size and, when needed, condenses the oldest material first: earlier tool results are summarised to what matters for
the question, then the conversation before the question becomes one summary. The chat shows a short status when this
happens. The current question and the latest results are never summarised; only when the latest results alone are too
large are they cut to fit, marked as cut. When even the question and the tools' descriptions do not fit, the agent
answers without its tools.

### Limits and approvals

A profile bounds how many decisions and tool calls one answer may take. At the limit, the agent answers with what it has
found and says that it stopped early. Any tool can be set to need the user's approval before it runs — every time, once
per answer, or once per conversation.

## What it does *not* do

- **It is not a fixed workflow.** The model decides which tools to use, so two similar questions may take different
  paths. For a guaranteed sequence, use the dedicated blueprints.
- **It does not replace the Document Intelligence Assistant's retrieval.** Its knowledge search is simpler: each
  database is searched with the embedding model it was indexed with and the results are reranked together, without the
  Document Intelligence Assistant's per-retriever tuning or grounding check.
- **It never reads what the user may not.** Collections the asking user cannot read are not offered, even when the
  profile lists them or the profile allows "every collection".
- **Its code sandbox is shared hardware.** Each user's sandbox home is separate, but all users share one container, so
  it is not a hard boundary between users; see [Coding](../../10_chat_ui/6_coding/).
- **No tools from external systems yet.** MCP tool servers and handing off to other agents are planned follow-ups; use
  the MCP Tool Agent for those today.

## Setting it up

1. **Grant the blueprint.** The Universal Agent is not part of a new tenant's default set; a sysadmin grants it (see
   [Access control](../../16_multi_tenancy/4_access_control/)).
2. **Create a profile.** In **Admin > Agents > Blueprints**, select **Universal Agent** and click **Create Profile**.
   Give it an Agent ID, a name, a description and an icon.
3. **Write the instructions.** Describe what this assistant is for and how it should answer. They are added after the
   built-in instructions on using tools, so you do not need to explain the tools.
4. **Choose the knowledge.** Under **Knowledge Tool**, either list the databases and collections it may search, or turn
   on **Every Collection the User Can Read**.
5. **Choose the model.** Pick a chat model that supports tool calls. The **Task LLM** condenses long conversations and
   writes titles and follow-up questions, so a smaller model is fine there.
6. **Review the limits and approvals** under **Tools**, then save.

## Configuration reference

### Behaviour

| Field                    | Default   | Description                                                                                   |
| ------------------------ | --------- | --------------------------------------------------------------------------------------------- |
| **Instructions**         | *(empty)* | What this assistant is for and how it should answer, added after the built-in instructions.   |
| **Maximum Input Tokens** | `128000`  | The input budget. The conversation is trimmed and, inside the tool loop, condensed to fit it. |

### Knowledge Tool

| Field                                  | Default | Description                                                                            |
| -------------------------------------- | ------- | -------------------------------------------------------------------------------------- |
| **Every Collection the User Can Read** | Off     | Offer every knowledge collection the asking user may read, instead of the listed ones. |
| **Collections**                        | —       | Databases the model may search, each whole or narrowed to some of its collections.     |

Under **Knowledge Search**, **Sections per Database** and the **Reranking Model** set how the search ranks what it
finds.

### Tools

| Field                  | Default | Description                                                                                           |
| ---------------------- | ------- | ----------------------------------------------------------------------------------------------------- |
| **Maximum Decisions**  | `10`    | How often the model may choose tools before it must answer.                                           |
| **Maximum Tool Calls** | `20`    | How many tool calls one answer may make in total.                                                     |
| **Disable Tools**      | Off     | Turn on to withhold some tools; the Disabled Tools picker appears only while it is on.                |
| **Disabled Tools**     | —       | Tools this profile never offers, while Disable Tools is on.                                           |
| **Approvals**          | —       | Tools whose calls the user must approve first: every call, once per answer, or once per conversation. |

### Knowledge Documents

| Field                       | Default   | Description                                                                                                       |
| --------------------------- | --------- | ----------------------------------------------------------------------------------------------------------------- |
| **Work on Whole Documents** | Off       | Offer the document tools and table extraction. Profiles saved before these tools existed keep them off.           |
| **Document Path Filter**    | *(empty)* | Only documents whose path matches this pattern, e.g. `invoices/**`. It limits the document tools, not the search. |

### Table Extraction

| Field                           | Default    | Description                                                                        |
| ------------------------------- | ---------- | ---------------------------------------------------------------------------------- |
| **Extraction Model**            | main model | The model that reads each document and extracts its rows.                          |
| **Files per Answer**            | `100`      | The most documents one extraction answer reads.                                    |
| **Minutes per Answer**          | `5`        | About how long one answer may extract before the rest is offered in parts.         |
| **Most Matching Documents**     | `1000`     | Above it, the user is only asked to narrow the request.                            |
| **Rows in the Table**           | `500`      | The most rows one answer shows; in a chat, at most 100, the rest on *continue*.    |
| **Longest Fully Read Document** | `500000`   | Longer documents (in characters) are read in their relevant parts, marked as such. |
| **Model Calls at Once**         | `4`        | Extraction calls one agent instance makes at the same time.                        |

Extraction behaves as in the [Knowledge Extraction Agent](../14_knowledge_extraction_agent/): a selection too large for
one answer gets a sample and the offer to narrow it or to continue in parts, and the model asks the user before it
continues. One answer continues at most one part, even when the user agreed to all of them, and an answer that showed a
sample continues none, so every answer stays within **Minutes per Answer** and the user confirms after seeing the
sample.

By default an extraction needs the user's approval in the chat. A client that cannot answer an approval, such as the
OpenAI-compatible API or a bot, stops there, so the shipped templates that offer extraction (**Knowledge Assistant** and
**Data Analyst**) set the **Extract a table** approval to *never*; the size check above still asks the user before a
large extraction. The **Workplace Assistant** template keeps the document tools off: it is the general everyday
assistant, its users rarely need a table across many documents, and fewer tools keep its choice of tool reliable.

Memory and attached-file settings are the same as on the other chat agents; see [Memory](../../15_memory/).
