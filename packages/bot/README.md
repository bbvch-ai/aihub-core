# Swiss AI Hub Bot

Bot integration SDK for the [Swiss AI Hub](https://github.com/bbvch-ai/aihub-core) platform. Connects users to Swiss AI
Hub agents through MS Teams, Slack, and web chat.

- **Multi-channel** — one `BaseChatBot` lifecycle with channel-specific handling for Teams, Slack, and WebChat.
- **Streaming & BITL** — token streaming plus bot-in-the-loop human-expert escalation back into agent workflows.
- **Conversation state** — per-endpoint configuration and conversation history persisted in MongoDB with TTL.

## Installation

```bash
pip install swiss-ai-hub-bot
```

This pulls in [`swiss-ai-hub-core`](https://pypi.org/project/swiss-ai-hub-core/).

## Usage

```python
from swiss_ai_hub.bot import BotRunner
```

## Links

- Source & issues: https://github.com/bbvch-ai/aihub-core
- Documentation: https://bbvch-ai.github.io/aihub-core/

## License

Apache-2.0
