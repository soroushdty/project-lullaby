from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


class SchemaContractError(Exception):
    pass


class SchemaTableMissingError(SchemaContractError):
    pass


class SchemaValidationConfigError(SchemaContractError):
    pass


@dataclass
class TableContract:
    table_name: str
    required_columns: list[str]
    optional_columns: list[str]
    primary_key: list[str]
    timestamp_column: str
    constraints: list[str] = field(default_factory=list)


class SchemaContract(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def version(self) -> str: ...

    @abstractmethod
    def table_names(self) -> list[str]: ...

    @abstractmethod
    def table_contract(self, table_name: str) -> TableContract: ...

    @abstractmethod
    def pandera_schema(self, table_name: str): ...

    @abstractmethod
    def data_dictionary(self, table_name: str) -> dict[str, dict]: ...
