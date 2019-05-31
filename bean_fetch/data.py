from dataclasses import dataclass
from typing import Mapping, Any, Optional, List, TypeVar, Generic, Type, Dict
from pathlib import Path
from enum import Enum
from abc import ABC

import yaml
from pydantic import Json
from pydantic.dataclasses import dataclass
from beancount.core.data import Transaction

Kind = TypeVar("Kind")


@dataclass(frozen=True)
class RawTx(Generic[Kind]):
    venue: str
    kind: Kind
    timestamp: str
    raw: Json
    meta: Optional[Mapping[str, str]] = None


Config = TypeVar("Config")


class VenueLike(Generic[Config, Kind], ABC):
    @staticmethod
    def fetch(config: Config) -> List[RawTx[Kind]]:
        ...

    @staticmethod
    def handles(tx: RawTx[Kind]) -> bool:
        ...

    @staticmethod
    def parse(config: Config, tx: RawTx[Kind]) -> Transaction:
        ...
