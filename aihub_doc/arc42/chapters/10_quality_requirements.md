# Quality requirements

Chapter 1 (Introduction and goals) established five quality goals ordered by stakeholder priority: data sovereignty,
transparency and auditability, vendor independence, operational self-sufficiency, and extensibility without platform
modification. This chapter refines those goals into concrete scenarios that can be evaluated against the architecture.

## Quality tree

The quality tree organizes requirements into categories. Each leaf references one or more scenarios in the next section.

- **Performance**
  - Response latency (PF-1)
  - Pipeline throughput (PF-2)
- **Security**
  - Authentication (SE-1)
  - Authorization granularity (SE-2)
  - Lateral movement prevention (SE-3)

## Quality scenarios

### Performance

**PF-1: Streaming response tokens reach the user within the LLM's time-to-first-token.** 

**PF-2: Document processing scales linearly with document count.** Each document is an independent Dagster partition.
Processing one document does not block or slow down any other document. A failure in one partition does not affect
others. 

### Security

**SE-1: Authentication supports multiple identity providers and token types.**
**SE-2: Permissions are granular to individual agent instances.**
**SE-3: Container compromise does not grant access to unrelated services.** 
