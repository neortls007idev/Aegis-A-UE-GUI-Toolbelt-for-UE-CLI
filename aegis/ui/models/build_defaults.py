"""Shared default build options."""

from __future__ import annotations

from typing import List

DEFAULT_CONFIGS: List[str] = [
    "Debug",
    "DebugGame",
    "DebugServer",
    "DebugEditor",
    "Development",
    "DevelopmentServer",
    "DevelopmentEditor",
    "Test",
    "TestServer",
    "TestEditor",
    "Shipping",
    "ShippingServer",
    "ShippingEditor",
]

DEFAULT_PLATFORMS: List[str] = ["Win64", "Linux", "Mac", "Android"]
