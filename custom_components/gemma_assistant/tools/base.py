"""Base class and registry for tools that the assistant can use."""
from __future__ import annotations

import abc
import logging
from typing import Any

_LOGGER = logging.getLogger(__name__)


class Tool(abc.ABC):
    """Abstract base class for an assistant tool."""

    # Underlining attributes are filled by subclasses
    name: str = ""
    description: str = ""
    # JSON schema describing the parameters (Ollama tools format)
    parameters: dict[str, Any] = {}

    def __init__(self, hass: Any) -> None:
        self.hass = hass

    @abc.abstractmethod
    async def async_call(self, **kwargs: Any) -> str:
        """Execute the tool and return a string result (to feed back to the LLM)."""
        raise NotImplementedError

    def to_ollama_tool(self) -> dict[str, Any]:
        """Serialize this tool in the format expected by Ollama."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters or {
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            },
        }


class ToolRegistry:
    """Holds all available tools and exposes them in Ollama format."""

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """Register a tool instance."""
        if not tool.name:
            raise ValueError("Tool must have a non-empty name")
        if tool.name in self._tools:
            _LOGGER.warning("Tool %s already registered, overwriting", tool.name)
        self._tools[tool.name] = tool
        _LOGGER.debug("Registered tool: %s", tool.name)

    def unregister(self, name: str) -> None:
        """Unregister a tool by name."""
        self._tools.pop(name, None)

    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def list_tools(self) -> list[Tool]:
        return list(self._tools.values())

    def to_ollama_tools(self) -> list[dict[str, Any]]:
        """Return all tools in Ollama format."""
        return [t.to_ollama_tool() for t in self._tools.values()]

    async def async_call(self, name: str, arguments: dict[str, Any]) -> str:
        """Call a tool by name with the given arguments."""
        tool = self.get(name)
        if tool is None:
            return f"Erreur: outil '{name}' inconnu."
        try:
            return await tool.async_call(**arguments)
        except Exception as err:  # noqa: BLE001
            _LOGGER.exception("Error while calling tool %s", name)
            return f"Erreur lors de l'exécution de l'outil {name}: {err}"
