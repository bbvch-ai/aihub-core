---
title: Deployment
index: 6
---

# :rocket: Deployment Guide

## :building_construction: Overview

The Swiss AI-Hub is a fully dockerized platform that can be deployed in multiple configurations to meet different
privacy, infrastructure, and budget requirements. All services, from databases to agents to pipelines, are containerized
for seamless deployment and scaling.

## :gear: Deployment Options

### :house: 1. Full On-Premises Deployment (GPU Required)

The most private and secure deployment option where everything runs entirely on your infrastructure.

::: info :shield: Maximum Privacy This setup provides complete data sovereignty - no data ever leaves your premises. All
processing, including LLM inference, happens on your own hardware. :::

#### Requirements

- **GPU**: NVIDIA RTX A6000 Ada (minimum) or NVIDIA A100 (recommended)
  - **Mistral Small 3.2**: Requires NVIDIA RTX A6000 Ada or better
  - **DeepSeek R1 Distilled Qwen 32B**: Requires NVIDIA A100
- **Memory**: Minimum 48 GB RAM
- **CPU**: Minimum 12 cores
- **Storage**: 256 GB fast SSD storage (minimum)

#### Configuration

Uses the GPU-enabled Docker Compose configuration that includes:

- vLLM server for local LLM hosting
- Complete AI-Hub infrastructure stack
- Choice of pre-configured LLMs based on available VRAM:
  - **Mistral Small 3.2**: High-performance reasoning and text generation
  - **DeepSeek R1 Distilled Qwen 32B**: Advanced reasoning model for complex tasks

::: details :whale: Deployment using docker compose

```bash
# Clone the repository
git clone https://github.com/bbvch-ai/aihub-core

# Navigate to the project directory
cd aihub-core

# Choose your deployment variant:
# For development (local Dockerfiles)
docker compose -f docker-compose-gpu.dev.yml up -d

# For production (recommended - latest stable images)
docker compose -f docker-compose-gpu.latest.yml up -d

# For bleeding edge (not recommended for production)
docker compose -f docker-compose-gpu.nightly.yml up -d
```

:::

::: details :arrows_clockwise: Automated Updates For production deployments, we recommend setting up a nightly job to
pull new images and restart the stack:

```bash
# Add to crontab for nightly updates
0 2 * * * cd /path/to/aihub-core && docker compose -f docker-compose-gpu.latest.yml pull && docker compose -f docker-compose-gpu.latest.yml up -d
```

:::

### :cloud: 2. On-Premises with External LLM Provider

Ideal for organizations that want to host the AI-Hub on their infrastructure but don't have GPU resources.

::: tip :balance_scale: Balanced Approach This configuration provides infrastructure control while leveraging external
LLM providers for AI capabilities. :::

#### Requirements

- **Hardware**: Server without GPU requirements
- **Memory**: Minimum 48 GB RAM
- **CPU**: Minimum 12 cores
- **Storage**: 256 GB fast SSD storage (minimum)
- **External LLM Provider**: OpenAI-compatible API endpoint

#### Recommended LLM Providers

**:switzerland: Swiss Provider (Recommended)**

- **Infomaniak**: Swiss-based provider offering the exact same models as the on-premises setup
  - **Mistral Small 3.2**: High-performance reasoning and text generation
  - **DeepSeek R1 Distilled Qwen 32B**: Advanced reasoning model for complex tasks
  - **Migration Advantage**: Seamless migration path to full on-premises deployment since models are identical

**:globe_with_meridians: International Providers**

- **Azure OpenAI**: Enterprise-grade with compliance features
- **Google Cloud AI**: Gemini models through Vertex AI
- **OpenAI API**: Direct access to GPT models
- **Any OpenAI-compatible provider**

::: details :whale: Deployment using docker compose

```bash
# Clone the repository
git clone https://github.com/bbvch-ai/aihub-core

# Configure environment variables for external LLM provider
cp .env.dev .env
# Edit .env with your LLM provider credentials

# Choose your deployment variant:
# For development (local Dockerfiles)
docker compose -f docker-compose.dev.yml up -d

# For production (recommended - latest stable images)
docker compose -f docker-compose.latest.yml up -d

# For bleeding edge (not recommended for production)
docker compose -f docker-compose.nightly.yml up -d
```

:::

### :cloud: 3. Cloud DIY Deployment

Deploy the AI-Hub in your preferred cloud provider (Azure, AWS, Google Cloud) while maintaining full control over the
infrastructure.

::: tip :cloud: Flexible Cloud Deployment This option provides cloud scalability and reliability while keeping you in
control of your deployment and data. :::

#### Requirements

- **Cloud Provider Account**: Azure, AWS, or Google Cloud
- **VM Specifications**: Equivalent to on-premises requirements
- **Network Configuration**: Proper security groups and networking
- **External LLM Provider**: OpenAI-compatible API endpoint

#### Example: Azure Deployment for ca. 50 Users

- **VM Size**: B12ms (12 vCPUs, 48 GB RAM)
- **Storage**: Premium SSD with 96 GB
- **Estimated Cost**: ~369 CHF/month for VM + LLM inference costs

::: details :whale: Deployment using docker compose

```bash
# After setting up your cloud VM, follow the same steps as on-premises
git clone https://github.com/bbvch-ai/aihub-core
cd aihub-core
docker compose -f docker-compose.latest.yml up -d
```

:::

### :cloud: 4. BBV Swiss AI Cloud (SaaS)

The BBV Swiss AI Cloud offers a fully managed AI-Hub experience where we handle all infrastructure, scaling, and
maintenance concerns. This solution is designed for organizations that want to focus entirely on their AI use cases
without worrying about the underlying technology stack.

**All servers are securely managed in :switzerland: Switzerland by Infomaniak!**

::: info :shield: Privacy-First SaaS Each customer receives a dedicated, completely isolated server instance in a Swiss
data center, ensuring 100% data privacy with zero cross-customer data sharing. :::

Your dedicated AI-Hub instance runs in our secure Swiss infrastructure, giving you all the benefits of the platform
without any of the operational overhead. We manage updates, scaling, security patches, and infrastructure monitoring,
while you retain full control over your data and AI workflows.

#### :hugs: What We Manage For You

- **Infrastructure Operations**: Server maintenance, updates, and monitoring
- **Scaling**: Automatic resource scaling based on your usage patterns
- **Security**: Regular security updates and compliance monitoring
- **LLM Provider Integration**: Seamless access to multiple AI providers through our centralized LiteLLM server
- **Data Protection**: Advanced anonymization before any data reaches third-party providers
- **Billing Management**: Consolidated monthly billing with detailed usage breakdowns

#### :speech_balloon: LLM Provider Ecosystem

Through our centralized LiteLLM server, you gain access to a curated selection of AI providers:

- **Swiss Providers**: Infomaniak for data sovereignty
- **High-Performance**: Groq for ultra-fast inference
- **Enterprise**: Azure OpenAI, AWS Google Cloud AI for enterprise features
- **Specialized**: Various providers for specific use cases

We handle all provider relationships, rate limiting, and failover scenarios, ensuring consistent service availability.

#### :moneybag: Pricing Structure

- **Platform Fee**: 9 CHF per user per month
- **Minimum Commitment**: 50 users (450 CHF/month base)
- **LLM Usage**: Pay-per-use billing for AI inference
- **No Hidden Costs**: Transparent pricing with detailed monthly reports

#### Getting Started

Contact BBV to discuss your requirements and set up your dedicated AI-Hub instance in the Swiss AI Cloud.

## :bar_chart: Deployment Comparison

### Cost Analysis (50 Users, CHF/Month)

| Deployment Type          | CapEx (Initial) | OpEx (Monthly) | Total Year 1 | Notes                                                 |
| ------------------------ | --------------- | -------------- | ------------ | ----------------------------------------------------- |
| **On-Premises (GPU)**    | 25,000 CHF      | 1,400 CHF      | 41,800 CHF   | Server: 20k, GPU: 5k / Electricity: 200, Admin: 1,200 |
| **On-Premises (No GPU)** | 8,000 CHF       | 1,600 CHF      | 27,200 CHF   | Server: 8k / Electricity: 150, Admin: 1,200, LLM: 250 |
| **Cloud DIY (Azure)**    | 0 CHF           | 1,819 CHF      | 21,828 CHF   | VM: 369, Admin: 1,200, LLM: 250                       |
| **BBV Swiss AI Cloud**   | 0 CHF           | 700 CHF        | 8,400 CHF    | Platform: 450, LLM: 250                               |

### Feature Comparison

| Feature                      | On-Premises (GPU)    | On-Premises (No GPU) | Cloud DIY             | BBV Swiss AI Cloud    |
| ---------------------------- | -------------------- | -------------------- | --------------------- | --------------------- |
| **Data Privacy**             | Maximum              | High                 | Medium                | High                  |
| **Setup Complexity**         | High                 | Medium               | Medium                | Minimal               |
| **Hardware Requirements**    | NVIDIA A100 + Server | Server Only          | None                  | None                  |
| **Scaling**                  | Manual Migration     | Manual Migration     | Manual/Auto           | Automatic             |
| **LLM Provider Flexibility** | Local Models Only    | Full Flexibility     | Full Flexibility      | Curated Selection     |
| **Maintenance**              | Self-managed         | Self-managed         | Self-managed          | Fully Managed         |
| **Compliance**               | Full Control         | Full Control         | Shared Responsibility | Shared Responsibility |

## :wrench: Technical Considerations

### :arrow_up: Scaling Self-Hosted Deployments

When hosting the AI-Hub yourself, scaling requires manual intervention:

1. **Monitor Resource Usage**: Track CPU, memory, and storage utilization
2. **Identify Bottlenecks**: Determine if scaling is needed
3. **Server Migration**: Move to larger instance when limits are reached
4. **Data Migration**: Ensure seamless data transfer during upgrades

### :lock: Security Best Practices

::: warning :warning: Security Checklist

- Keep Docker images updated
- Implement proper network segmentation
- Use strong authentication mechanisms
- Regular security audits and monitoring
- Backup strategies for critical data :::

## :books: Next Steps

1. **Choose Your Deployment Option**: Based on privacy requirements, budget, and infrastructure capabilities
2. **Review Requirements**: Ensure hardware and software prerequisites are met
3. **Prepare Environment**: Set up necessary infrastructure and credentials
4. **Deploy**: Follow the specific deployment instructions for your chosen option
5. **Configure**: Customize the AI-Hub for your organization's needs
6. **Test**: Verify all components are working correctly
7. **Monitor**: Implement ongoing monitoring and maintenance procedures

For detailed configuration and troubleshooting, refer to the specific deployment documentation for your chosen option.
