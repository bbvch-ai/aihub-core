---
title: User feedback
---

# User feedback

Users can rate AI responses through thumbs up/down controls during conversations. This feedback helps evaluate model
performance and can inform future improvements.

## How feedback works

Users leave a thumbs up for responses they like or a thumbs down for responses they don't. The system captures a
snapshot of the chat when users provide ratings.

Feedback can happen in two modes. Arena mode randomly selects models for unbiased comparison. When rating in arena mode,
giving a thumbs up to one response automatically assigns a thumbs down to the alternative response.

Normal interaction mode lets users rate responses during standard chat without special activation. For leaderboard
impact in this mode, responses need to come from different models for comparison.

## Leaderboard and rankings

Ratings feed into a personalized leaderboard using an Elo rating system similar to chess rankings. This shows which
models perform best based on actual usage.

The platform supports topic-based reranking through tagging. Users can compare model performance across specific domains
like customer service or technical support. Topic tagging happens automatically with manual override options for
accurate categorization.

## Data handling

All evaluation data stays on the user's instance by default. Organizations control whether to opt in for community
sharing. Captured feedback can support future model fine-tuning efforts.

The feedback system helps organizations identify which models work best for their specific use cases and where
improvements might be needed.
