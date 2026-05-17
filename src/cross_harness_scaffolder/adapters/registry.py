"""Registry for live harness adapters."""
from __future__ import annotations

from .base import HarnessAdapter


class HarnessAdapterRegistry:
    def __init__(self) -> None:
        self._adapters: dict[str, HarnessAdapter] = {}

    def register(self, name: str, adapter: HarnessAdapter) -> None:
        self._adapters[name.lower()] = adapter

    def get(self, name: str) -> HarnessAdapter:
        try:
            return self._adapters[name.lower()]
        except KeyError as exc:
            raise KeyError(f"no adapter registered for {name}") from exc

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._adapters))
