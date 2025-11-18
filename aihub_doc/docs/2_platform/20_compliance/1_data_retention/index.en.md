---
title: Data Retention Policies
---

## Data retention strategy

The platform implements a tiered retention strategy:

**Ephemeral data (30-day automatic deletion)**: High-performance working memory stored in Redis expires automatically.
Execution-specific data provides a fixed 30-day window for debugging. Conversational memory uses a sliding 30-day
expiration that resets with each access.

**Workflow events (dual constraints)**: NATS JetStream manages workflow events with both time-based (30 days) and
capacity-based (10 million messages) limits. In high-throughput deployments, events may be deleted before the 30-day
limit when capacity is reached.

**Permanent storage (manual lifecycle management)**: NoSQL storage retains conversation history indefinitely without
automatic expiration. Organizations must implement explicit data lifecycle policies aligned with regulatory requirements
and business needs.

**Operational implications**: Organizations have a 30-day window for forensic analysis of workflow execution details.
Critical execution information should be persisted to permanent storage before the 30-day threshold for long-term
retention. Compliance investigations requiring workflow reconstruction are limited to the available retention window.
