# SonarCloud Issues Report

**Project:** aihub-core_lib-core
**Generated:** 2025-07-29 15:02:26 UTC
**Total Issues:** 71

## Summary

### By Severity

| Severity | Count |
|----------|-------|
| CRITICAL | 33 |
| INFO | 2 |
| MAJOR | 12 |
| MINOR | 24 |

### By Type

| Type | Count |
|------|-------|
| BUG | 1 |
| CODE_SMELL | 70 |

### By Status

| Status | Count |
|--------|-------|
| OPEN | 71 |

## Issues Details

### CRITICAL Issues (33)

#### 1. AZgty-_EVrCR02s6g8S9

**Rule:** `python:S3776`
**Type:** CODE_SMELL
**Status:** OPEN
**File:** `aihub_lib/routes/chat/ChatService.py`
**Line:** 75
**Technical Debt:** 8min
**Assignee:** thommann@github
**Tags:** architecture, brain-overload

**Message:**
> Refactor this function to reduce its Cognitive Complexity from 18 to the 15 allowed.

---

#### 2. AZgulhWGR8pPJSSuhkyq

**Rule:** `python:S3776`
**Type:** CODE_SMELL
**Status:** OPEN
**File:** `aihub_lib/generative_ai/utils/combine_nodes_in_order.py`
**Line:** 40
**Technical Debt:** 31min
**Tags:** architecture, brain-overload

**Message:**
> Refactor this function to reduce its Cognitive Complexity from 41 to the 15 allowed.

---

#### 3. AZgORXZw2oVXgTfKX0WK

**Rule:** `python:S1192`
**Type:** CODE_SMELL
**Status:** OPEN
**File:** `aihub_lib/persistence/messaging/entities/PersistedProcessEventEntity.py`
**Line:** 64
**Technical Debt:** 6min
**Assignee:** joelbarmettlerUZH@github
**Tags:** design

**Message:**
> Define a constant instead of duplicating this literal "$match" 3 times.

---

#### 4. AZgORXGN2oVXgTfKX0WI

**Rule:** `python:S3776`
**Type:** CODE_SMELL
**Status:** OPEN
**File:** `aihub_lib/nats/events/work_request/human/HumanWorkRequestEvent.py`
**Line:** 69
**Technical Debt:** 7min
**Assignee:** joelbarmettlerUZH@github
**Tags:** architecture, brain-overload

**Message:**
> Refactor this function to reduce its Cognitive Complexity from 17 to the 15 allowed.

---

#### 5. AZfqCbEAGb5URIl7G19c

**Rule:** `python:S1192`
**Type:** CODE_SMELL
**Status:** OPEN
**File:** `aihub_lib/auth/access/AccessChecker.py`
**Line:** 33
**Technical Debt:** 8min
**Assignee:** joelbarmettlerUZH@github
**Tags:** design

**Message:**
> Define a constant instead of duplicating this literal "aihub.admin." 4 times.

---

#### 6. AZfqCbEAGb5URIl7G19d

**Rule:** `python:S1192`
**Type:** CODE_SMELL
**Status:** OPEN
**File:** `aihub_lib/auth/access/AccessChecker.py`
**Line:** 34
**Technical Debt:** 10min
**Assignee:** joelbarmettlerUZH@github
**Tags:** design

**Message:**
> Define a constant instead of duplicating this literal "aihub.user." 5 times.

---

#### 7. AZfqoK_-N5EV8T44z-Aq

**Rule:** `python:S3776`
**Type:** CODE_SMELL
**Status:** OPEN
**File:** `aihub_lib/nats/events/BaseEvent.py`
**Line:** 238
**Technical Debt:** 28min
**Assignee:** joelbarmettlerUZH@github
**Tags:** architecture, brain-overload

**Message:**
> Refactor this function to reduce its Cognitive Complexity from 38 to the 15 allowed.

---

#### 8. AZfqoK7-N5EV8T44z-Ap

**Rule:** `python:S3776`
**Type:** CODE_SMELL
**Status:** OPEN
**File:** `aihub_lib/nats/events/semantic/llm/Message.py`
**Line:** 76
**Technical Debt:** 11min
**Assignee:** joelbarmettlerUZH@github
**Tags:** architecture, brain-overload

**Message:**
> Refactor this function to reduce its Cognitive Complexity from 21 to the 15 allowed.

---

#### 9. AZe_sobs_MuCJu3zxQbD

**Rule:** `python:S3776`
**Type:** CODE_SMELL
**Status:** OPEN
**File:** `aihub_lib/nats/workflow/annotations/extractors/extract_event_classes.py`
**Line:** 8
**Technical Debt:** 8min
**Assignee:** joelbarmettlerUZH@github
**Tags:** architecture, brain-overload

**Message:**
> Refactor this function to reduce its Cognitive Complexity from 18 to the 15 allowed.

---

#### 10. AZdfhPXKKNbEtBTtwg0b

**Rule:** `python:S3776`
**Type:** CODE_SMELL
**Status:** OPEN
**File:** `aihub_lib/generative_ai/document/parsers/RecursiveSummaryParser.py`
**Line:** 115
**Technical Debt:** 26min
**Tags:** architecture, brain-overload

**Message:**
> Refactor this function to reduce its Cognitive Complexity from 36 to the 15 allowed.

---

#### 11. AZdfhPXKKNbEtBTtwg0c

**Rule:** `python:S3776`
**Type:** CODE_SMELL
**Status:** OPEN
**File:** `aihub_lib/generative_ai/document/parsers/RecursiveSummaryParser.py`
**Line:** 243
**Technical Debt:** 6min
**Tags:** architecture, brain-overload

**Message:**
> Refactor this function to reduce its Cognitive Complexity from 16 to the 15 allowed.

---

#### 12. AZb90ggY5LMTL3ROQlLp

**Rule:** `python:S1192`
**Type:** CODE_SMELL
**Status:** OPEN
**File:** `aihub_lib/persistence/messaging/entities/PersistedAgentEventEntity.py`
**Line:** 203
**Technical Debt:** 6min
**Assignee:** joelbarmettlerUZH@github
**Tags:** design

**Message:**
> Define a constant instead of duplicating this literal "$event_type" 3 times.

---

#### 13. AZb90ggY5LMTL3ROQlLq

**Rule:** `python:S1192`
**Type:** CODE_SMELL
**Status:** OPEN
**File:** `aihub_lib/persistence/messaging/entities/PersistedAgentEventEntity.py`
**Line:** 217
**Technical Debt:** 22min
**Assignee:** joelbarmettlerUZH@github
**Tags:** design

**Message:**
> Define a constant instead of duplicating this literal "$cond" 11 times.

---

#### 14. AZdBNvgR-ip6uM6QSDMB

**Rule:** `python:S3776`
**Type:** CODE_SMELL
**Status:** OPEN
**File:** `aihub_lib/generative_ai/document/parsers/MarkdownStructuralNodeParser.py`
**Line:** 165
**Technical Debt:** 7min
**Tags:** architecture, brain-overload

**Message:**
> Refactor this function to reduce its Cognitive Complexity from 17 to the 15 allowed.

---

#### 15. AZawWkDTaqHQVS73BF4m

**Rule:** `python:S1192`
**Type:** CODE_SMELL
**Status:** OPEN
**File:** `aihub_lib/persistence/messaging/entities/PersistedAgentEventEntity.py`
**Line:** 194
**Technical Debt:** 8min
**Assignee:** joelbarmettlerUZH@github
**Tags:** design

**Message:**
> Define a constant instead of duplicating this literal "$group" 4 times.

---

#### 16. AZawWkDTaqHQVS73BF4p

**Rule:** `python:S1192`
**Type:** CODE_SMELL
**Status:** OPEN
**File:** `aihub_lib/persistence/messaging/entities/PersistedAgentEventEntity.py`
**Line:** 196
**Technical Debt:** 24min
**Assignee:** joelbarmettlerUZH@github
**Tags:** design

**Message:**
> Define a constant instead of duplicating this literal "$first" 12 times.

---

#### 17. AZawWkDTaqHQVS73BF4r

**Rule:** `python:S1192`
**Type:** CODE_SMELL
**Status:** OPEN
**File:** `aihub_lib/persistence/messaging/entities/PersistedAgentEventEntity.py`
**Line:** 198
**Technical Debt:** 12min
**Assignee:** joelbarmettlerUZH@github
**Tags:** design

**Message:**
> Define a constant instead of duplicating this literal "$event_time" 6 times.

---

#### 18. AZawWkDTaqHQVS73BF4q

**Rule:** `python:S1192`
**Type:** CODE_SMELL
**Status:** OPEN
**File:** `aihub_lib/persistence/messaging/entities/PersistedAgentEventEntity.py`
**Line:** 199
**Technical Debt:** 24min
**Assignee:** joelbarmettlerUZH@github
**Tags:** design

**Message:**
> Define a constant instead of duplicating this literal "$event_parents" 12 times.

---

#### 19. AZawWkDTaqHQVS73BF4s

**Rule:** `python:S1192`
**Type:** CODE_SMELL
**Status:** OPEN
**File:** `aihub_lib/persistence/messaging/entities/PersistedAgentEventEntity.py`
**Line:** 200
**Technical Debt:** 8min
**Assignee:** joelbarmettlerUZH@github
**Tags:** design

**Message:**
> Define a constant instead of duplicating this literal "$agent_class" 4 times.

---

#### 20. AZawWkDTaqHQVS73BF4t

**Rule:** `python:S1192`
**Type:** CODE_SMELL
**Status:** OPEN
**File:** `aihub_lib/persistence/messaging/entities/PersistedAgentEventEntity.py`
**Line:** 201
**Technical Debt:** 6min
**Assignee:** joelbarmettlerUZH@github
**Tags:** design

**Message:**
> Define a constant instead of duplicating this literal "$agent_id" 3 times.

---

#### 21. AZawWkDTaqHQVS73BF4u

**Rule:** `python:S3776`
**Type:** CODE_SMELL
**Status:** OPEN
**File:** `aihub_lib/persistence/messaging/entities/PersistedAgentEventEntity.py`
**Line:** 445
**Technical Debt:** 20min
**Assignee:** joelbarmettlerUZH@github
**Tags:** architecture, brain-overload

**Message:**
> Refactor this function to reduce its Cognitive Complexity from 30 to the 15 allowed.

---

#### 22. AZawWkDTaqHQVS73BF4l

**Rule:** `python:S1192`
**Type:** CODE_SMELL
**Status:** OPEN
**File:** `aihub_lib/persistence/messaging/entities/PersistedAgentEventEntity.py`
**Line:** 187
**Technical Debt:** 8min
**Assignee:** joelbarmettlerUZH@github
**Tags:** design

**Message:**
> Define a constant instead of duplicating this literal "$toDate" 4 times.

---

#### 23. AZawWkDTaqHQVS73BF4n

**Rule:** `python:S1192`
**Type:** CODE_SMELL
**Status:** OPEN
**File:** `aihub_lib/persistence/messaging/entities/PersistedAgentEventEntity.py`
**Line:** 187
**Technical Debt:** 10min
**Assignee:** joelbarmettlerUZH@github
**Tags:** design

**Message:**
> Define a constant instead of duplicating this literal "$addFields" 5 times.

---

#### 24. AZawWkDTaqHQVS73BF4o

**Rule:** `python:S1192`
**Type:** CODE_SMELL
**Status:** OPEN
**File:** `aihub_lib/persistence/messaging/entities/PersistedAgentEventEntity.py`
**Line:** 187
**Technical Debt:** 6min
**Assignee:** joelbarmettlerUZH@github
**Tags:** design

**Message:**
> Define a constant instead of duplicating this literal "$divide" 3 times.

---

#### 25. AZe_soce_MuCJu3zxQbP

**Rule:** `python:S3776`
**Type:** CODE_SMELL
**Status:** OPEN
**File:** `aihub_lib/nats/workflow/visualizers/WorkflowVisualizer.py`
**Line:** 298
**Technical Debt:** 8min
**Assignee:** joelbarmettlerUZH@github
**Tags:** architecture, brain-overload

**Message:**
> Refactor this function to reduce its Cognitive Complexity from 18 to the 15 allowed.

---

#### 26. AZakvTK3-2P-EKD-hu8l

**Rule:** `python:S1192`
**Type:** CODE_SMELL
**Status:** OPEN
**File:** `aihub_lib/persistence/messaging/entities/PersistedAgentEventEntity.py`
**Line:** 256
**Technical Debt:** 6min
**Assignee:** joelbarmettlerUZH@github
**Tags:** design

**Message:**
> Define a constant instead of duplicating this literal "$ifNull" 3 times.

---

#### 27. AZakvTK3-2P-EKD-hu8k

**Rule:** `python:S1192`
**Type:** CODE_SMELL
**Status:** OPEN
**File:** `aihub_lib/persistence/messaging/entities/PersistedAgentEventEntity.py`
**Line:** 285
**Technical Debt:** 6min
**Assignee:** joelbarmettlerUZH@github
**Tags:** design

**Message:**
> Define a constant instead of duplicating this literal "$first_event_time" 3 times.

---

#### 28. AZakvTK3-2P-EKD-hu8i

**Rule:** `python:S1192`
**Type:** CODE_SMELL
**Status:** OPEN
**File:** `aihub_lib/persistence/messaging/entities/PersistedAgentEventEntity.py`
**Line:** 286
**Technical Debt:** 6min
**Assignee:** joelbarmettlerUZH@github
**Tags:** design

**Message:**
> Define a constant instead of duplicating this literal "$latest_event_time" 3 times.

---

#### 29. AZYkwBwoKYz75SMJz4Rn

**Rule:** `python:S3776`
**Type:** CODE_SMELL
**Status:** OPEN
**File:** `aihub_lib/generative_ai/open_webui/sdk/client.py`
**Line:** 67
**Technical Debt:** 9min
**Assignee:** joelbarmettlerUZH@github
**Tags:** brain-overload

**Message:**
> Refactor this function to reduce its Cognitive Complexity from 19 to the 15 allowed.

---

#### 30. AZe_soce_MuCJu3zxQbN

**Rule:** `python:S3776`
**Type:** CODE_SMELL
**Status:** OPEN
**File:** `aihub_lib/nats/workflow/visualizers/WorkflowVisualizer.py`
**Line:** 251
**Technical Debt:** 10min
**Assignee:** joelbarmettlerUZH@github
**Tags:** architecture, brain-overload

**Message:**
> Refactor this function to reduce its Cognitive Complexity from 20 to the 15 allowed.

---

#### 31. AZe_soce_MuCJu3zxQbR

**Rule:** `python:S3776`
**Type:** CODE_SMELL
**Status:** OPEN
**File:** `aihub_lib/nats/workflow/visualizers/WorkflowVisualizer.py`
**Line:** 361
**Technical Debt:** 26min
**Assignee:** joelbarmettlerUZH@github
**Tags:** architecture, brain-overload

**Message:**
> Refactor this function to reduce its Cognitive Complexity from 36 to the 15 allowed.

---

#### 32. AZe_soex_MuCJu3zxQbS

**Rule:** `python:S3776`
**Type:** CODE_SMELL
**Status:** OPEN
**File:** `aihub_lib/nats/dispatcher/stores/event/JetStreamEventStore.py`
**Line:** 94
**Technical Debt:** 6min
**Assignee:** joelbarmettlerUZH@github
**Tags:** architecture, brain-overload

**Message:**
> Refactor this function to reduce its Cognitive Complexity from 16 to the 15 allowed.

---

#### 33. AZRBDmhSbHc6ZoOz7ymQ

**Rule:** `python:S3776`
**Type:** CODE_SMELL
**Status:** OPEN
**File:** `aihub_lib/persistence/messaging/entities/PersistedAgentEventEntity.py`
**Line:** 353
**Technical Debt:** 11min
**Assignee:** joelbarmettlerUZH@github
**Tags:** brain-overload

**Message:**
> Refactor this function to reduce its Cognitive Complexity from 21 to the 15 allowed.

---

### MAJOR Issues (12)

#### 1. AZhB2Z2fa-kF7SeDpXNX

**Rule:** `python:S112`
**Type:** CODE_SMELL
**Status:** OPEN
**File:** `aihub_lib/generative_ai/document/accessor/S3AnonymousFileAccessService.py`
**Line:** 81
**Technical Debt:** 20min
**Assignee:** joelbarmettlerUZH@github
**Tags:** cwe, error-handling

**Message:**
> Replace this generic exception class with a more specific one.

---

#### 2. AZfqoLB5N5EV8T44z-Ar

**Rule:** `python:S5890`
**Type:** CODE_SMELL
**Status:** OPEN
**File:** `aihub_lib/nats/dispatcher/stores/event/ExecutionContextEventStore.py`
**Line:** 12
**Technical Debt:** 5min
**Assignee:** joelbarmettlerUZH@github
**Tags:** confusing, typing

**Message:**
> Replace the type hint "defaultdict[str, dict[str, BaseEvent]]" with "Optional[defaultdict[str, dict[str, BaseEvent]]]" or don't assign "None" to "events"

---

#### 3. AZfF-tsxr2d-Y8XHjmnI

**Rule:** `python:S5890`
**Type:** CODE_SMELL
**Status:** OPEN
**File:** `aihub_lib/auth/dependencies/DangerousDevelopmentOnlyAuthHandler/DangerousDevelopmentOnlyAuthConfig.py`
**Line:** 32
**Technical Debt:** 5min
**Assignee:** joelbarmettlerUZH@github
**Tags:** confusing, typing

**Message:**
> Assign to "ROLES" a value of type "list[str]" instead of "str" or update its type hint.

---

#### 4. AZfF-tpIr2d-Y8XHjmnH

**Rule:** `python:S5890`
**Type:** CODE_SMELL
**Status:** OPEN
**File:** `aihub_lib/generative_ai/document/types/IngestedDocument.py`
**Line:** 30
**Technical Debt:** 5min
**Assignee:** joelbarmettlerUZH@github
**Tags:** confusing, typing

**Message:**
> Replace the type hint "str" with "Optional[str]" or don't assign "None" to "content"

---

#### 5. AZe_soX3_MuCJu3zxQa-

**Rule:** `python:S5799`
**Type:** CODE_SMELL
**Status:** OPEN
**File:** `aihub_lib/nats/events/work/agent/AgentWorkEvent.py`
**Line:** 33
**Technical Debt:** 1min
**Assignee:** joelbarmettlerUZH@github
**Tags:** confusing, suspicious

**Message:**
> Merge these implicitly concatenated strings; or did you forget a comma?

---

#### 6. AZe_soX3_MuCJu3zxQa_

**Rule:** `python:S5799`
**Type:** CODE_SMELL
**Status:** OPEN
**File:** `aihub_lib/nats/events/work/agent/AgentWorkEvent.py`
**Line:** 51
**Technical Debt:** 1min
**Assignee:** joelbarmettlerUZH@github
**Tags:** confusing, suspicious

**Message:**
> Merge these implicitly concatenated strings; or did you forget a comma?

---

#### 7. AZe_soZA_MuCJu3zxQbA

**Rule:** `python:S5799`
**Type:** CODE_SMELL
**Status:** OPEN
**File:** `aihub_lib/nats/events/work/process/ProcessWorkEvent.py`
**Line:** 34
**Technical Debt:** 1min
**Assignee:** joelbarmettlerUZH@github
**Tags:** confusing, suspicious

**Message:**
> Merge these implicitly concatenated strings; or did you forget a comma?

---

#### 8. AZe_soZA_MuCJu3zxQbB

**Rule:** `python:S5799`
**Type:** CODE_SMELL
**Status:** OPEN
**File:** `aihub_lib/nats/events/work/process/ProcessWorkEvent.py`
**Line:** 52
**Technical Debt:** 1min
**Assignee:** joelbarmettlerUZH@github
**Tags:** confusing, suspicious

**Message:**
> Merge these implicitly concatenated strings; or did you forget a comma?

---

#### 9. AZeDLDi2dBM_Tn0OZG3m

**Rule:** `python:S7493`
**Type:** BUG
**Status:** OPEN
**File:** `aihub_lib/generative_ai/open_webui/sdk/api/files.py`
**Line:** 62
**Technical Debt:** 5min
**Assignee:** joelbarmettlerUZH@github
**Tags:** anyio, async, asyncio, trio

**Message:**
> Use an asynchronous file API instead of synchronous open() in this async function.

---

#### 10. AZYkwBv8KYz75SMJz4Rm

**Rule:** `python:S5890`
**Type:** CODE_SMELL
**Status:** OPEN
**File:** `aihub_lib/generative_ai/open_webui/sdk/models/chats.py`
**Line:** 105
**Technical Debt:** 5min
**Assignee:** joelbarmettlerUZH@github
**Tags:** confusing, typing

**Message:**
> Replace the type hint "ChatHistory" with "Optional[ChatHistory]" or don't assign "None" to "history"

---

#### 11. AZe_soex_MuCJu3zxQbT

**Rule:** `python:S7483`
**Type:** CODE_SMELL
**Status:** OPEN
**File:** `aihub_lib/nats/dispatcher/stores/event/JetStreamEventStore.py`
**Line:** 256
**Technical Debt:** 5min
**Assignee:** joelbarmettlerUZH@github
**Tags:** anyio, async, asyncio, trio

**Message:**
> Remove this "timeout" parameter and use a timeout context manager instead.

---

#### 12. AZe_sobS_MuCJu3zxQbC

**Rule:** `python:S1542`
**Type:** CODE_SMELL
**Status:** OPEN
**File:** `aihub_lib/nats/workflow/annotations/custom_types/ListOfSize.py`
**Line:** 44
**Technical Debt:** 10min
**Assignee:** joelbarmettlerUZH@github
**Tags:** convention, pep

**Message:**
> Rename function "FixedList" to match the regular expression ^[a-z_][a-z0-9_]*$.

---

### MINOR Issues (24)

#### 1. AZfznaNkdS77XbRtQJS5

**Rule:** `python:S7508`
**Type:** CODE_SMELL
**Status:** OPEN
**File:** `aihub_lib/nats/events/BaseEvent.py`
**Line:** 99
**Technical Debt:** 5min
**Assignee:** thommann@github

**Message:**
> Remove this redundant call.

---

#### 2. AZfAIIQq_xk4es7yM4sR

**Rule:** `python:S7508`
**Type:** CODE_SMELL
**Status:** OPEN
**File:** `aihub_lib/auth/identity/AzureIdentityProvider/AzureGraphService.py`
**Line:** 221
**Technical Debt:** 5min
**Assignee:** joelbarmettlerUZH@github

**Message:**
> Remove this redundant call.

---

#### 3. AZe_sofl_MuCJu3zxQbY

**Rule:** `python:S7503`
**Type:** CODE_SMELL
**Status:** OPEN
**File:** `aihub_lib/nats/dispatcher/BaseDispatcher.py`
**Line:** 239
**Technical Debt:** 5min
**Assignee:** joelbarmettlerUZH@github
**Tags:** async

**Message:**
> Use asynchronous features in this function or remove the `async` keyword.

---

#### 4. AZe_soex_MuCJu3zxQbW

**Rule:** `python:S7503`
**Type:** CODE_SMELL
**Status:** OPEN
**File:** `aihub_lib/nats/dispatcher/stores/event/JetStreamEventStore.py`
**Line:** 331
**Technical Debt:** 5min
**Assignee:** joelbarmettlerUZH@github
**Tags:** async

**Message:**
> Use asynchronous features in this function or remove the `async` keyword.

---

#### 5. AZe_socK_MuCJu3zxQbE

**Rule:** `python:S7494`
**Type:** CODE_SMELL
**Status:** OPEN
**File:** `aihub_lib/nats/workflow/DispatchableWorkflow.py`
**Line:** 74
**Technical Debt:** 5min
**Assignee:** joelbarmettlerUZH@github

**Message:**
> Replace set constructor call with a set comprehension.

---

#### 6. AZe_socK_MuCJu3zxQbF

**Rule:** `python:S7494`
**Type:** CODE_SMELL
**Status:** OPEN
**File:** `aihub_lib/nats/workflow/DispatchableWorkflow.py`
**Line:** 84
**Technical Debt:** 5min
**Assignee:** joelbarmettlerUZH@github

**Message:**
> Replace set constructor call with a set comprehension.

---

#### 7. AZeDLDradBM_Tn0OZG3r

**Rule:** `python:S7503`
**Type:** CODE_SMELL
**Status:** OPEN
**File:** `aihub_lib/generative_ai/evaluation/PhoenixExperimentEvaluator.py`
**Line:** 168
**Technical Debt:** 5min
**Assignee:** joelbarmettlerUZH@github
**Tags:** async

**Message:**
> Use asynchronous features in this function or remove the `async` keyword.

---

#### 8. AZeDLDwVdBM_Tn0OZG3s

**Rule:** `python:S7508`
**Type:** CODE_SMELL
**Status:** OPEN
**File:** `aihub_lib/nats/events/BaseEvent.py`
**Line:** 118
**Technical Debt:** 5min
**Assignee:** joelbarmettlerUZH@github

**Message:**
> Remove this redundant call.

---

#### 9. AZe_soce_MuCJu3zxQbO

**Rule:** `python:S117`
**Type:** CODE_SMELL
**Status:** OPEN
**File:** `aihub_lib/nats/workflow/visualizers/WorkflowVisualizer.py`
**Line:** 300
**Technical Debt:** 2min
**Assignee:** joelbarmettlerUZH@github
**Tags:** convention

**Message:**
> Rename this parameter "G" to match the regular expression ^[_a-z][a-z0-9_]*$.

---

#### 10. AZeDLDoTdBM_Tn0OZG3p

**Rule:** `python:S7503`
**Type:** CODE_SMELL
**Status:** OPEN
**File:** `aihub_lib/generative_ai/guards/context_sufficient_guard.py`
**Line:** 37
**Technical Debt:** 5min
**Tags:** async

**Message:**
> Use asynchronous features in this function or remove the `async` keyword.

---

#### 11. AZeDLDlGdBM_Tn0OZG3n

**Rule:** `python:S7503`
**Type:** CODE_SMELL
**Status:** OPEN
**File:** `aihub_lib/generative_ai/open_webui/sdk/client.py`
**Line:** 67
**Technical Debt:** 5min
**Assignee:** joelbarmettlerUZH@github
**Tags:** async

**Message:**
> Use asynchronous features in this function or remove the `async` keyword.

---

#### 12. AZe_soce_MuCJu3zxQbG

**Rule:** `python:S117`
**Type:** CODE_SMELL
**Status:** OPEN
**File:** `aihub_lib/nats/workflow/visualizers/WorkflowVisualizer.py`
**Line:** 86
**Technical Debt:** 2min
**Assignee:** joelbarmettlerUZH@github
**Tags:** convention

**Message:**
> Rename this parameter "G" to match the regular expression ^[_a-z][a-z0-9_]*$.

---

#### 13. AZe_soce_MuCJu3zxQbH

**Rule:** `python:S117`
**Type:** CODE_SMELL
**Status:** OPEN
**File:** `aihub_lib/nats/workflow/visualizers/WorkflowVisualizer.py`
**Line:** 222
**Technical Debt:** 2min
**Assignee:** joelbarmettlerUZH@github
**Tags:** convention

**Message:**
> Rename this parameter "END_NODE" to match the regular expression ^[_a-z][a-z0-9_]*$.

---

#### 14. AZe_soce_MuCJu3zxQbI

**Rule:** `python:S117`
**Type:** CODE_SMELL
**Status:** OPEN
**File:** `aihub_lib/nats/workflow/visualizers/WorkflowVisualizer.py`
**Line:** 222
**Technical Debt:** 2min
**Assignee:** joelbarmettlerUZH@github
**Tags:** convention

**Message:**
> Rename this parameter "G" to match the regular expression ^[_a-z][a-z0-9_]*$.

---

#### 15. AZe_soce_MuCJu3zxQbJ

**Rule:** `python:S117`
**Type:** CODE_SMELL
**Status:** OPEN
**File:** `aihub_lib/nats/workflow/visualizers/WorkflowVisualizer.py`
**Line:** 222
**Technical Debt:** 2min
**Assignee:** joelbarmettlerUZH@github
**Tags:** convention

**Message:**
> Rename this parameter "START_NODE" to match the regular expression ^[_a-z][a-z0-9_]*$.

---

#### 16. AZe_soce_MuCJu3zxQbL

**Rule:** `python:S117`
**Type:** CODE_SMELL
**Status:** OPEN
**File:** `aihub_lib/nats/workflow/visualizers/WorkflowVisualizer.py`
**Line:** 253
**Technical Debt:** 2min
**Assignee:** joelbarmettlerUZH@github
**Tags:** convention

**Message:**
> Rename this parameter "G" to match the regular expression ^[_a-z][a-z0-9_]*$.

---

#### 17. AZe_soce_MuCJu3zxQbM

**Rule:** `python:S117`
**Type:** CODE_SMELL
**Status:** OPEN
**File:** `aihub_lib/nats/workflow/visualizers/WorkflowVisualizer.py`
**Line:** 256
**Technical Debt:** 2min
**Assignee:** joelbarmettlerUZH@github
**Tags:** convention

**Message:**
> Rename this parameter "START_NODE" to match the regular expression ^[_a-z][a-z0-9_]*$.

---

#### 18. AZe_soce_MuCJu3zxQbK

**Rule:** `python:S117`
**Type:** CODE_SMELL
**Status:** OPEN
**File:** `aihub_lib/nats/workflow/visualizers/WorkflowVisualizer.py`
**Line:** 257
**Technical Debt:** 2min
**Assignee:** joelbarmettlerUZH@github
**Tags:** convention

**Message:**
> Rename this parameter "END_NODE" to match the regular expression ^[_a-z][a-z0-9_]*$.

---

#### 19. AZe_soce_MuCJu3zxQbQ

**Rule:** `python:S117`
**Type:** CODE_SMELL
**Status:** OPEN
**File:** `aihub_lib/nats/workflow/visualizers/WorkflowVisualizer.py`
**Line:** 344
**Technical Debt:** 2min
**Assignee:** joelbarmettlerUZH@github
**Tags:** convention

**Message:**
> Rename this parameter "G" to match the regular expression ^[_a-z][a-z0-9_]*$.

---

#### 20. AZeDLDwVdBM_Tn0OZG3t

**Rule:** `python:S7504`
**Type:** CODE_SMELL
**Status:** OPEN
**File:** `aihub_lib/nats/events/BaseEvent.py`
**Line:** 256
**Technical Debt:** 5min
**Assignee:** joelbarmettlerUZH@github

**Message:**
> Remove this unnecessary `list()` call on an already iterable object.

---

#### 21. AZe_soex_MuCJu3zxQbU

**Rule:** `python:S7503`
**Type:** CODE_SMELL
**Status:** OPEN
**File:** `aihub_lib/nats/dispatcher/stores/event/JetStreamEventStore.py`
**Line:** 305
**Technical Debt:** 5min
**Assignee:** joelbarmettlerUZH@github
**Tags:** async

**Message:**
> Use asynchronous features in this function or remove the `async` keyword.

---

#### 22. AZe_soex_MuCJu3zxQbV

**Rule:** `python:S7503`
**Type:** CODE_SMELL
**Status:** OPEN
**File:** `aihub_lib/nats/dispatcher/stores/event/JetStreamEventStore.py`
**Line:** 318
**Technical Debt:** 5min
**Assignee:** joelbarmettlerUZH@github
**Tags:** async

**Message:**
> Use asynchronous features in this function or remove the `async` keyword.

---

#### 23. AZeDLDm0dBM_Tn0OZG3o

**Rule:** `python:S7503`
**Type:** CODE_SMELL
**Status:** OPEN
**File:** `aihub_lib/generative_ai/guards/few_shot_guard.py`
**Line:** 26
**Technical Debt:** 5min
**Tags:** async

**Message:**
> Use asynchronous features in this function or remove the `async` keyword.

---

#### 24. AZeDLDpFdBM_Tn0OZG3q

**Rule:** `python:S7503`
**Type:** CODE_SMELL
**Status:** OPEN
**File:** `aihub_lib/generative_ai/guards/agent_description_guard.py`
**Line:** 27
**Technical Debt:** 5min
**Tags:** async

**Message:**
> Use asynchronous features in this function or remove the `async` keyword.

---

### INFO Issues (2)

#### 1. AZgORXNq2oVXgTfKX0WJ

**Rule:** `python:S1135`
**Type:** CODE_SMELL
**Status:** OPEN
**File:** `aihub_lib/nats/distributor/ExternalProcessEventDistributor.py`
**Line:** 43
**Technical Debt:** 0min
**Assignee:** joelbarmettlerUZH@github
**Tags:** cwe

**Message:**
> Complete the task associated to this "TODO" comment.

---

#### 2. AZewKTHRupWWaP7h9eFF

**Rule:** `python:S1135`
**Type:** CODE_SMELL
**Status:** OPEN
**File:** `aihub_lib/generative_ai/document/loaders/DocumentIntelligenceLoader.py`
**Line:** 107
**Technical Debt:** 0min
**Tags:** cwe

**Message:**
> Complete the task associated to this "TODO" comment.

---
