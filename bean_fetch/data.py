from datetime import datetime
from typing import Mapping, Optional, List, TypeVar, Generic
from abc import ABC

from pydantic import Json
from pydantic.dataclasses import dataclass
from beancount.core.data import Transaction

Kind = TypeVar("Kind")


@dataclass(frozen=True)
class RawTx(Generic[Kind]):
    venue: str
    kind: Kind
    timestamp: datetime
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
