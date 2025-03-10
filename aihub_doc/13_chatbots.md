# 13. Chatbots

## Overview

In the AI-Hub, chatbots serve as the critical interface where humans and AI agents come together on a single, unified platform. By bridging human interactions with automated agent workflows, chatbots empower users to collaborate directly with intelligent systems—enabling real-time assistance, decision support, and seamless escalation when necessary.

## Design Philosophy

The chatbots in the AI-Hub are designed to ensure that both humans and AI agents share the same platform and interface, fostering collaboration and a cohesive user experience. This integration minimizes friction between automated processes and human oversight, allowing users to interact with agents in a familiar, conversational manner. Key design tenets include:
- **Unified Interaction Platform:** Humans and agents interact within a shared environment, ensuring that manual interventions, real-time monitoring, and autonomous workflows coexist seamlessly.
- **Standardized Communication:** The chatbots employ a standardized messaging format, enabling smooth and predictable interactions across all channels.

## Technical Implementation

### Azure Bot Service and Multi-Channel Support

Chatbots leverage the Azure Bot Service to manage communications across multiple channels—whether it’s Microsoft Teams, Slack, web chat, or other supported platforms. This multi-channel capability ensures that users can access the AI-Hub's services from their preferred interface without compromising functionality or consistency.

### Bot API Architecture

The Bot API, a core component of the chatbots, is built using FastAPI and Python alongside the Microsoft Bot Framework SDK. This combination delivers a robust, scalable, and maintainable API that:
- **Receives Messages in a Standardized Format:** Messages arriving from the Azure Bot Service follow a uniform structure, enabling the API to process text, speech, images, and files efficiently.
- **Supports Multimodal Input:** Bots are equipped to handle diverse input types, ensuring that users can communicate through text, voice, images, or file uploads without any loss of context or functionality.
- **Delivers Structured Output:** Beyond simple text responses, the Bot API supports structured outputs such as Cards, which present information in rich, interactive formats complete with images, buttons, and visual cues for enhanced engagement.

### Integration with AI Agent Workflows

Once the Bot API receives a message from the Azure Bot Service, it transforms the input into events that are injected into the AI-Hub's event-driven architecture. This process:
- **Triggers Agent Workflows:** The standardized message is routed to the appropriate AI agent workflows, ensuring that the processing logic remains consistent with the rest of the platform.
- **Maintains Context:** Conversation state is preserved through thread and run contexts, allowing for multi-turn dialogues where the AI agent can refer back to previous interactions to provide accurate and contextually relevant responses.
- **Enables Human Collaboration:** When necessary, the system can escalate issues from the AI agent to human operators, ensuring that complex or ambiguous queries receive the appropriate level of attention.

## User Experience

### Seamless Human-Agent Collaboration

By unifying the interface for both human users and AI agents, the AI-Hub ensures that every interaction is coherent and context-aware. Users benefit from:
- **Consistent Interactions Across Channels:** Whether communicating via web chat, mobile devices, or collaboration platforms like Teams, the experience remains uniform and intuitive.
- **Multimodal Communication:** Users can switch between text, speech, image uploads, and file sharing without needing to adjust their communication style.
- **Enhanced Visual Responses:** With support for structured output such as Cards, responses can be rich with context, including images, links, and interactive elements, making interactions more informative and engaging.

### Empowering Both Automated and Human Processes

This unified approach not only simplifies the user experience—it also enhances operational efficiency. Automated workflows are supported by AI agents that work transparently alongside human oversight, ensuring that:
- Routine tasks are handled automatically.
- Escalations to human operators are smooth and integrated into the same communication flow.
- The overall system remains flexible and responsive to both automated intelligence and human judgment.

## Deploying Chatbots Using the Python Setup Script

The AI-Hub provides a Python setup script to help deploy your chatbot in an Azure environment with minimal local dependencies. While you can run most components locally, the Azure Bot Service remains essential for managing multi-channel communications.

This [script](../aihub_bot/aihub_bot/setup_azure_bot.py) automates several deployment tasks:
- **Azure AD App Registration:** It creates an Azure AD application for the bot and resets its credentials to generate an `appId` and `app_password`.
- **Bot Resource Creation:** Using the provided API URL and API path, the script configures the Azure Bot resource, specifying parameters such as resource group, bot name, location, and SKU.
- **Credential Storage:** It saves the bot’s credentials in a MongoDB or Cosmos DB instance, which can later be used for authentication and authorization.

### Required Inputs and How to Obtain Them

- **Resource Group (--resource-group):**  
  The name of your Azure resource group. Create one via the Azure portal if it does not already exist.

- **Bot Name (--bot-name):**  
  The desired name for your bot. This will be used as both the resource and display name.

- **API URL (--api-url) and API Path (--api-path):**  
  These define the endpoint where your bot’s API is hosted. For local setups, you can use tools like ngrok to expose your local server (e.g., `https://example.ngrok.io/api/messages`).

- **Location (--location):**  
  The Azure region for deployment (default is typically `westeurope`).

- **Tenant ID (--tenant-id):**  
  (Optional) Your Azure tenant ID for a single-tenant configuration. Retrieve this from the Azure Active Directory section in the Azure portal. If omitted, a multi-tenant setup is assumed.

- **SKU (--sku):**  
  The pricing tier for the bot service (default is `F0` for the free tier).

For credential storage, choose one of the following:
- **MongoDB Connection (--mongo-connection-string):**  
  Provide your MongoDB connection string if using a local or cloud-based MongoDB instance.
- **Cosmos DB Parameters (--cosmos-name and --subscription-id):**  
  Alternatively, specify your Cosmos DB account name and Azure subscription ID to store credentials in Cosmos DB.
- *Important:* Ensure that your Bot API can access the chosen database for retrieving the stored credentials.

### Channel Configuration

While the setup script handles the core deployment tasks, channel integrations must be configured manually:
- **Manual Addition of Channels:**  
  After creating the Azure Bot resource, you must add channels (such as Slack or Microsoft Teams) through the Azure portal or via each channel’s dedicated configuration interface.
- **Channel Counterparts:**  
  For each channel you wish to integrate, create the corresponding application in that channel’s ecosystem. For example:
  - For **Slack**, create a Slack App at [Slack API](https://api.slack.com/apps) and obtain credentials (client ID, client secret, and signing secret).
  - For **Microsoft Teams**, register your bot with the Microsoft Bot Framework Developer Portal and secure the necessary credentials.
  
  These channel-specific credentials are then linked to your Azure Bot Service to enable seamless multi-channel communication.
