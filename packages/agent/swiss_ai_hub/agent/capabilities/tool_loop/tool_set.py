import asyncio
from typing import Annotated, Any, Literal

from llama_index.core.base.llms.types import ChatMessage
from llama_index.core.tools import BaseTool
from llama_index.core.tools.tool_spec.base import BaseToolSpec
from pydantic import BaseModel, ConfigDict, Field
from swiss_ai_hub.core.agents import AgentConfig
from swiss_ai_hub.core.events.agent import ChatFeature, RunToolLoopEvent, ToolDefinition, ToolLoopMode

from swiss_ai_hub.agent.capabilities.tool_loop.tool_context import ToolContext
from swiss_ai_hub.agent.capabilities.tool_loop.tool_options import ToolOptions


class ToolSet(BaseModel):
    """The tools one of a blueprint's loops may offer, declared as a class attribute and named after it.

    ```python
    class WeatherAgent(Agent):
        research = ToolLoop.over(WebSearch, WeatherTools)

        @step()
        async def loop_step(self, ctx: Conversation.Contextualized) -> ToolLoop.RunRequest:
            return WeatherAgent.research.run(ctx.history)
    ```

    Three kinds of tool, the same to the model: capabilities that offer a tool (their calls run the capability's
    own steps), LlamaIndex tool specs (each listed method a tool, built per run with the run's `ToolContext`), and
    LlamaIndex tools. Declaring a capability here is what installs it.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: Annotated[str, Field(description="The attribute the set is declared under; the loop's name.")] = "tools"
    capabilities: Annotated[list[Any], Field(description="Capability classes offering a tool.")] = []
    specs: Annotated[list[Any], Field(description="LlamaIndex tool spec classes.")] = []
    functions: Annotated[list[Any], Field(description="LlamaIndex tools.")] = []

    def __set_name__(self, owner: type, name: str) -> None:
        self.name = name

    @classmethod
    def of(cls, tools: tuple[Any, ...]) -> "ToolSet":
        capabilities, specs, functions = [], [], []
        for tool in tools:
            if isinstance(tool, BaseTool):
                functions.append(tool)
            elif isinstance(tool, type) and issubclass(tool, BaseToolSpec):
                specs.append(tool)
            elif getattr(tool, "tool_name", None):
                capabilities.append(tool)
            else:
                msg = f"{tool!r} is no tool: pass a capability offering one, a LlamaIndex tool spec or a tool."
                raise ValueError(msg)
        tool_set = cls(capabilities=capabilities, specs=specs, functions=functions)
        names = tool_set.names()
        if len(names) != len(set(names)):
            msg = f"Tool names must be unique within a tool set, got {names}"
            raise ValueError(msg)
        return tool_set

    def run(
        self,
        history: list[ChatMessage],
        mode: ToolLoopMode = ToolLoopMode.ANSWER,
        cite_sources: bool = True,
        tools: list[str] | None = None,
    ) -> RunToolLoopEvent:
        """Let the model decide which of these tools to use; `tools` narrows them for this call."""
        return RunToolLoopEvent(loop=self.name, history=history, mode=mode, cite_sources=cite_sources, tools=tools)

    def route(self, history: list[ChatMessage], cite_sources: bool = True) -> RunToolLoopEvent:
        """One decision: the model picks the tools worth running now, and their results come back as context."""
        return RunToolLoopEvent(
            loop=self.name, history=history, mode=ToolLoopMode.GATHER, cite_sources=cite_sources, max_iterations=1
        )

    def names(self) -> list[str]:
        return [
            *(capability.tool_name for capability in self.capabilities),
            *(self._spec_function_name(entry) for spec in self.specs for entry in spec.spec_functions),
            *(tool.metadata.name for tool in self.functions),
        ]

    def kind(self, name: str) -> Literal["capability", "function"] | None:
        if any(capability.tool_name == name for capability in self.capabilities):
            return "capability"
        return "function" if name in self.names() else None

    def source(self, name: str) -> object:
        """What defines the tool: its capability, its spec's method or the tool itself."""
        capability = next((c for c in self.capabilities if c.tool_name == name), None)
        if capability:
            return capability
        spec = next((spec for spec in self.specs if name in map(self._spec_function_name, spec.spec_functions)), None)
        if spec:
            return getattr(spec, name)
        return next(tool for tool in self.functions if tool.metadata.name == name)

    def options(self, name: str) -> ToolOptions:
        capability = next((c for c in self.capabilities if c.tool_name == name), None)
        if capability:
            return capability.tool_options.model_copy(update={"chat_feature": capability.chat_feature})
        for spec in self.specs:
            if name in [self._spec_function_name(entry) for entry in spec.spec_functions]:
                return ToolOptions.of_function(getattr(spec, name))
        tool = next((tool for tool in self.functions if tool.metadata.name == name), None)
        return ToolOptions.of_function(getattr(tool, "async_fn", None) or getattr(tool, "fn", None))

    def chat_features(self) -> set[ChatFeature]:
        return {self.options(name).chat_feature for name in self.names()} - {None}

    def function_tools(self, context: ToolContext) -> dict[str, BaseTool]:
        """This run's function tools, the specs built with its context so they can use its config and user."""
        tools = [*(tool for spec in self.specs for tool in spec(context).to_tool_list()), *self.functions]
        return {tool.metadata.name: tool for tool in tools}

    async def definitions(self, agent_config: AgentConfig, context: ToolContext) -> dict[str, ToolDefinition]:
        """Every tool the model could be offered on this profile; a capability with nothing to do offers none."""
        definitions = {}
        for capability in self.capabilities:
            definition = await asyncio.to_thread(capability.tool_definition, agent_config, context.t.locale)
            if definition is not None:
                definitions[definition.name] = definition
        for name, tool in self.function_tools(context).items():
            function = tool.metadata.to_openai_tool()["function"]
            definitions[name] = ToolDefinition(
                name=name, description=function["description"], parameters=function["parameters"]
            )
        return definitions

    @staticmethod
    def _spec_function_name(entry: str | tuple[str, str]) -> str:
        return entry if isinstance(entry, str) else entry[0]
