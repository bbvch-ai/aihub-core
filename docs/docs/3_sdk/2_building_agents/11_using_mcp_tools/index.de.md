---
title: MCP-Tools verwenden
description: Verbinden Sie Agents mit externen MCP-Servern und lassen Sie diese die von diesen Servern bereitgestellten Tools aufrufen.
source_sha: "a55ae06217e875bc66fad58766012494441a555581c4d1ac556ef64a9920718f"
---

# MCP-Tools verwenden

Agents sind nicht auf die von Ihnen geschriebenen Schritte und das von Ihnen indizierte Wissen beschränkt – sie können auch Tools auf **externen MCP-Servern** aufrufen. Das [Model Context Protocol](https://modelcontextprotocol.io) ist ein offener Standard zum Bereitstellen von Tools und Daten für KI-Anwendungen. Ein Agent verbindet sich mit jedem MCP-Server und lässt sein LLM die von ihm angebotenen Tools aufrufen: ein Ticket erstellen, eine Datenbank abfragen, eine Nachricht senden.

## Die Verbindungskonfiguration

`McpClientConfig` beschreibt eine einzelne MCP-Server-Verbindung. Es ist eine `StepConfig`, sodass der Dispatcher sie in jeden Schritt injiziert, der sie als Parameter deklariert – fügen Sie sie Ihrer Agent-Konfiguration hinzu, und sie wird in Ihrem Workflow verfügbar.

| Feld        | Zweck                                                                                |
| ----------- | ------------------------------------------------------------------------------------ |
| `name`      | Ein logischer Name für die Verbindung.                                               |
| `url`       | Der MCP-Server-Endpunkt – FastMCP leitet den Transport ab.                           |
| `auth_mode` | Wie authentifiziert werden soll: `none`, `api_key` oder `user_token`.                |
| `api_key`   | Der statische Schlüssel, der nur verwendet wird, wenn `auth_mode` `api_key` ist.     |
| `timeout`   | Client-Timeout in Sekunden.                                                          |

## Authentifizierungsmodi

| Modus        | Verhalten                                                                                                                              |
| ------------ | -------------------------------------------------------------------------------------------------------------------------------------- |
| `none`       | Es werden keine Anmeldeinformationen gesendet.                                                                                         |
| `api_key`    | Ein auf der Verbindung konfigurierter statischer Schlüssel wird als Bearer-Token gesendet.                                             |
| `user_token` | Das Token des anfragenden Benutzers wird weitergeleitet, sodass die externe Aktion diesem Benutzer zugeschrieben wird.               |

Der `user_token`-Modus funktioniert nur für vom Benutzer initiierte Chat-Läufe, die das Token des Benutzers enthalten. Geplante, prozessinitiierte, Bot-Kanal- und Agent-zu-Agent-Läufe leiten kein Benutzer-Token weiter und schlagen in diesem Modus fehl – verwenden Sie `api_key` oder `none` für diese.

## MCP-Tools von einem Schritt aus aufrufen

Fügen Sie ein `McpClientConfig`-Feld zu Ihrer Agent-Konfiguration hinzu und öffnen Sie dann einen Client innerhalb eines Schritts mit `McpClientFactory`. `McpAuthResolver` liest das weitergeleitete Benutzer-Token aus dem Run-Kontext, sodass eine auf den `user_token`-Modus eingestellte Verbindung im Namen des anfragenden Benutzers agiert.

```python
from swiss_ai_hub.core.mcp import McpClientConfig
from swiss_ai_hub.agent.mcp import McpAuthResolver, McpClientFactory


class ResearchAgentConfig(AgentConfig):
    mcp: McpClientConfig


class ResearchAgent(Agent):
    @step()
    async def call_tools(
        self,
        event: UserMessageEvent,
        mcp_config: McpClientConfig,
        run_context: RunContext,
    ) -> StopEvent:
        user_token = await McpAuthResolver.resolve_user_token(run_context)
        async with McpClientFactory.create(mcp_config, user_token=user_token) as mcp_client:
            tools = await mcp_client.list_tools()
            result = await mcp_client.call_tool("create_ticket", {"title": "..."})
        ...
```

::: warning
`McpClientFactory` löst einen Fehler aus, wenn `auth_mode` `api_key` oder `user_token` ist, aber die Anmeldeinformationen fehlen. Eine falsch konfigurierte Verbindung schlägt laut fehl, anstatt den Server stillschweigend unauthentifiziert oder mit der falschen Identität aufzurufen.
:::

## Der vorgefertigte McpReactAgent

Wenn Sie lediglich einen Agent benötigen, der über die Tools eines MCP-Servers nachdenkt, liefert das SDK den **`McpReactAgent`** – einen vollständigen ReAct-Stil-Agent, der die Tools und Ressourcen eines MCP-Servers entdeckt, das LLM sie in einer Schleife auswählen und aufrufen lässt und das Ergebnis streamt. Richten Sie dessen `McpClientConfig` auf Ihren Server, wählen Sie einen `auth_mode` und führen Sie ihn aus. Er ist auch die Referenzimplementierung für das obige Muster.
