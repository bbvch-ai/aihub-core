from abc import ABC, abstractmethod
from typing import Dict, Optional, Type

from aihub_lib.i18n.LocaleString import LocaleString


class IAgentConfig(ABC):
    """
    Interface for AgentConfig, describing the necessary attributes and methods for an agent configuration.
    """

    @property
    @abstractmethod
    def agent_id(self) -> str:
        """The ID of the agent."""
        pass

    @property
    @abstractmethod
    def name(self) -> LocaleString:
        """The name of the agent."""
        pass

    @property
    @abstractmethod
    def description(self) -> LocaleString:
        """The description of the agent."""
        pass

    @property
    @abstractmethod
    def system_prompt(self) -> LocaleString:
        """The system prompt of the agent."""
        pass

    @property
    @abstractmethod
    def color(self) -> Optional[str]:
        """The color of the agent's UI theme."""
        pass

    @property
    @abstractmethod
    def voice(self) -> Optional[str]:
        """The TTS voice ID the agent uses."""
        pass
