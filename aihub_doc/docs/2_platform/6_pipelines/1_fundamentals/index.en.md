---
title: Fundamentals
index: 2
---

# Pipeline Fundamentals

Data pipelines are the backbone of your AI's knowledge, responsible for the automated and continuous synchronization of information between your source systems and the AI's knowledge base. They are the robust, reliable workflows that ensure your AI agents operate with information that is always current, accurate, and secure.

This section explores the core principles behind the platform's data pipeline architecture, explaining how they are built, what they can do, and why they are essential for enterprise-grade AI.

## The Purpose of a Pipeline: Continuous Synchronization

In a dynamic business environment, information is constantly changing. A new policy is published, a technical manual is updated, a project status report is revised. A static knowledge base, updated only periodically, quickly becomes a liability, leading to AI-driven decisions based on outdated information.

Data pipelines solve this problem through **continuous synchronization**. They are persistent, automated processes that monitor your designated data sources, such as a SharePoint site or a network drive. When a document is added, modified, or deleted, the pipeline automatically detects the change and propagates it through the entire processing chain, ensuring the AI's knowledge base perfectly mirrors the state of your source systems.

::: info What is an "AI-Ready" Knowledge Base?
An AI-ready knowledge base isn't just a collection of files. It's a highly structured vector database where documents have been parsed, broken into meaningful chunks, and converted into numerical representations (embeddings). This allows AI agents to perform semantic searches based on meaning, not just keywords. The entire process of creating and maintaining this specialized database is managed by data pipelines.
:::

## Built on a Foundation of Code and Control

The Swiss AI Hub's pipelines are built on **Dagster**, a modern, enterprise-grade orchestration framework. This is a deliberate choice that provides immense flexibility and control. Because pipelines are defined as code (Python), they are not simple "connect-the-dots" workflows but powerful, programmable assets.

This code-based approach enables sophisticated capabilities that are out of reach for many visual-only platforms:
- **Custom Processing Logic**: You can implement specialized steps tailored to your unique content types, business rules, or quality standards.
- **Conditional Workflows**: The pipeline's path can change based on a document's content, source, or classification. For example, a contract might go through an extra PII-redaction step that a public manual would skip.
- **Robust Error Handling**: You can define precise logic for handling network issues, data anomalies, or temporary system failures, ensuring pipelines are resilient and don't require manual intervention for common problems.

This makes your pipelines reusable assets that encode your organization's specific knowledge about how to handle its data.

## Lifecycle Management: More Than Just Adding Data

A truly synchronized system must handle the full lifecycle of information. Our pipelines maintain complete fidelity with your source systems.

-   **When a document is added**, the pipeline processes it and adds the corresponding embeddings to the knowledge base.
-   **When a document is modified**, the pipeline intelligently removes all outdated embeddings associated with the old version before adding the new ones.
-   **When a document is deleted**, the pipeline purges all of its associated embeddings from the knowledge base.

This rigorous lifecycle management is critical. It prevents AI agents from retrieving information from old versions of documents or, worse, from documents that have been officially retired.

## Enterprise Connectivity and Extensibility

The platform provides a rich set of pre-built connectors for the systems where your organization's knowledge already lives. This allows for seamless integration without requiring complex data migration projects.

::: details Supported Data Source Categories
- **Enterprise Collaboration Platforms**: Natively connect to sources like Microsoft SharePoint, OneDrive, Confluence, and Jira.
- **File Systems**: Ingest data from network drives, local storage, or cloud storage like Azure Blob and S3.
- **Web Sources**: Scrape and process content from public websites, technical documentation portals, or industry news feeds.
:::

Crucially, the architecture is extensible. If you have a proprietary internal system or a specialized database, you can develop a custom connector, allowing the platform to integrate any information source relevant to your AI workflows.

## Governance and Quality Assurance: A Security-First Approach

Data pipelines are more than just data movers; they are the first line of defense for the quality and security of your AI's knowledge. They incorporate sophisticated governance and quality assurance mechanisms directly into the workflow.

-   **Content Validation**: Pipelines can inspect incoming data for quality and completeness. A document that is missing a critical section might be quarantined for human review instead of being automatically ingested.
-   **Security Scanning**: You can integrate automated checks for malicious content or policy violations, preventing harmful information from entering the knowledge base.
-   **Data Sanitization**: Pipelines can automatically apply transformation rules to redact sensitive information (like names or social security numbers) or enforce data classification policies before content becomes accessible to agents.

Every action taken by a pipeline—from the initial retrieval to the final quality check—is logged, creating a comprehensive audit trail that supports compliance reporting and forensic analysis. This ensures you always have a clear record of how your AI's knowledge was built.