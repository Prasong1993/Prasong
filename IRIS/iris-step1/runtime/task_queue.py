"""Small adapter registry; no dynamic imports or shell execution."""
from __future__ import annotations
from typing import Callable, Any

Adapter = Callable[[dict[str, Any]], dict[str, Any]]
_ADAPTERS: dict[str, Adapter] = {}

def register_adapter(kind: str, adapter: Adapter) -> None:
    if not kind.strip() or not callable(adapter):
        raise ValueError("A non-empty kind and callable adapter are required")
    _ADAPTERS[kind] = adapter

def unregister_adapter(kind: str) -> None:
    _ADAPTERS.pop(kind, None)

def get_adapter(kind: str) -> Adapter | None:
    return _ADAPTERS.get(kind)

def clear_adapters() -> None:
    _ADAPTERS.clear()
