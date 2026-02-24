---
title: Pipeline Fundamentals
---

# Pipeline Fundamentals

The AI-Hub Pipeline SDK is built on [Dagster](https://docs.dagster.io/). This page introduces the essential building
blocks that form every pipeline.

## Assets: The Data

An **asset** is the central concept in a pipeline. It represents a specific piece of data, such as a set of parsed
documents or a collection of vector embeddings. The code you write for an asset is the function that produces this data.

- **`@asset` / `@graph_asset`**: These decorators define a function as an asset. A `graph_asset` is a special type
  composed of multiple smaller operations (`@op`) wired together.
- **Role**: Assets define the "what" of your pipeline—the transformations that turn raw files into valuable, AI-ready
  data.

## I/O Managers

An **I/O Manager** handles the physical storage and retrieval of assets. They are the "plumbing" that connects one asset
to the next.

- **What they do**: When an asset produces data (e.g., a `RefDocDocument`), its I/O manager is responsible for saving it
  to a specific storage system (like MongoDB). When a downstream asset needs that data, the I/O manager knows how to
  load it.
- **Role**: I/O Managers abstract away storage logic. Your asset code doesn't need to know *where* or *how* data is
  stored, making your pipeline highly modular and easy to reconfigure.

## Resources: The External Connections

A **Resource** manages the connection to an external system, such as a database, an API, or a file store.

- **What they do**: Resources handle the configuration, authentication, and connection clients needed to interact with
  the outside world. For example, the `MongoDocumentStoreResource` manages the connection string and client for talking
  to MongoDB.
- **Role**: Resources separate your pipeline's logic from its environment configuration, allowing the same pipeline code
  to run seamlessly across development, testing, and production.

______________________________________________________________________

## Core Architectural Principles

- Instead of running entire pipelines on a fixed schedule, the SDK uses **observable source assets**. These assets
  monitor a data source (like an S3 bucket) and only trigger downstream processing when a file is added or changed. This
  is highly efficient, saving time and compute resources.
- Each document is processed in its own **partition**. This means a failure in one document won't halt the entire
  pipeline. The other documents will continue processing independently. This also allows for massive parallelism, as
  Dagster can process many partitions at once.
- To reduce boilerplate and enforce consistency, the SDK relies heavily on the **factory pattern**. Instead of writing
  complex asset and resource definitions from scratch, you use simple factory functions (e.g., `documents_factory`,
  `default_definitions`) that generate fully configured pipeline components for you.

## Next Steps

Now that you understand the fundamental components, explore the **[Core Pipeline Patterns](../2_core_patterns/)** to see
how these concepts are implemented in code to build powerful workflows.
