"""Tools package for Gemma Assistant."""
from __future__ import annotations

from .base import Tool, ToolRegistry
from .datetime_tool import DateTimeTool
from .homeassistant import HomeAssistantTool
from .search import SearXNGTool

__all__ = [
    "Tool",
    "ToolRegistry",
    "DateTimeTool",
    "HomeAssistantTool",
    "SearXNGTool",
]


def build_default_registry(hass) -> ToolRegistry:
    """Build the default registry with all built-in tools."""
    registry = ToolRegistry()
    registry.register(DateTimeTool(hass))
    registry.register(SearXNGTool(hass))
    registry.register(HomeAssistantTool(hass))
    return registry
