from dataclasses import dataclass
from typing import Mapping, Any, Optional, List, TypeVar, Generic, Type, Dict
from pathlib import Path
from enum import Enum
from abc import ABC

import yaml
from beancount.core.data import Transaction


@dataclass(frozen=True)
class RawTx:
    venue: str
    kind: Enum
    timestamp: str
    raw: Dict[str, Any]
    meta: Optional[Mapping[str, str]] = None


C = TypeVar("C")


class VenueLike(Generic[C], ABC):
    @staticmethod
    def fetch(config: C) -> List[RawTx]:
        ...

    @staticmethod
    def handles(tx: RawTx) -> bool:
        ...

    @staticmethod
    def parse(config: C, tx: RawTx) -> Transaction:
        ...
