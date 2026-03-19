# Framework for Infrastructure Deployment

## Context

There should be a clear way to describe and deploy the infrastructure. This helps to understand the system.
Infrastructure as Code (IaC) components should be able to be shared between different deployment units.

## Decision Drivers

- **Ease of Use** The infrastructure code should be easy to learn, use and read.
- **Maintainability** The infrastructure code should be easy to maintain, meaning that duplication should be avoided.

## Decision

We'll use Pulumi as the framework for Infrastructure as Code (IaC). Pulumi allows us to write Infrastructure as Code in
different Programming Languages. We use Python for this project. This makes it easy to understand as it is using the
same language. Since it builds up on e.g. python the infrastructure code can also be structured in method and classes
which makes it easier to avoid duplication and make the code easier to read and maintain as it can be structured in a
more modular way.

## Consequences

Pulumi in contrast to previously used Bicep manages its own state of an infrastructure by itself so it knows what needs
to be deployed and what already exists. This means this state needs to be persisted somewhere. Also, it must be ensured
that the state of pulumi represents what the state of the actual infrastructure is. Generating a drift between actual
infrastructure and pulumi state can lead to problems and should be avoided.
