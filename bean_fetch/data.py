from dataclasses import dataclass
from typing import Mapping, Any, Optional, List, TypeVar, Generic, Type
from pathlib import Path
from enum import Enum
from abc import ABC
from beancount.core.data import Transaction


@dataclass(frozen=True)
class Globals:
    archive_dir: Path
    base_currency: str


@dataclass(frozen=True)
class Tag:
    venue: str
    kind: Enum


@dataclass(frozen=True)
class RawTx:
    tag: Tag
    raw: Mapping[str, Any]
    meta: Optional[Mapping[str, str]] = None


Config = TypeVar("Config")


class Venue(Generic[Config], ABC):
    @staticmethod
    def fetch(config: Config) -> List[RawTx]:
        ...

    @staticmethod
    def handles(tag: Tag) -> bool:
        ...

    @staticmethod
    def parse(config: Config, tx: RawTx) -> Transaction:
        ...
