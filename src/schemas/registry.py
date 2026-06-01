from __future__ import annotations

import importlib

from src.schemas.base import SchemaContract, SchemaContractError

_ALIASES: dict[str, str] = {
    "lullaby": "src.schemas.lullaby:LullabySchema",
}


def resolve(selector: str) -> SchemaContract:
    """Return an instantiated SchemaContract for the given alias or import path."""
    dotted = _ALIASES.get(selector, selector)
    if ":" not in dotted:
        raise SchemaContractError(
            f"Cannot resolve schema '{selector}': use alias or 'package.module:ClassName'"
        )
    module_path, class_name = dotted.rsplit(":", 1)
    try:
        module = importlib.import_module(module_path)
    except ModuleNotFoundError as exc:
        raise SchemaContractError(f"Module not found: {module_path}") from exc
    cls = getattr(module, class_name, None)
    if cls is None:
        raise SchemaContractError(f"Class '{class_name}' not found in '{module_path}'")
    try:
        instance = cls()
    except TypeError as exc:
        raise SchemaContractError(
            f"Schema class '{selector}' cannot be instantiated without arguments: {exc}"
        ) from exc
    _assert_contract(instance, selector)
    return instance


def _assert_contract(instance: object, selector: str) -> None:
    required = ["name", "version", "table_names", "table_contract", "pandera_schema", "data_dictionary"]
    for attr in required:
        if not hasattr(instance, attr):
            raise SchemaContractError(
                f"Schema '{selector}' is missing required attribute: {attr}"
            )
