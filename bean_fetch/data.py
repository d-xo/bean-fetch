from datetime import datetime
from typing import Mapping, Optional, List, TypeVar, Generic
from abc import ABC

from pydantic import Json
from pydantic.dataclasses import dataclass
from dataclasses_json import dataclass_json
from beancount.core.data import Transaction

Config = TypeVar("Config")
Kind = TypeVar("Kind")


@dataclass_json
@dataclass(frozen=True)
class RawTx(Generic[Kind]):
    venue: str
    kind: Kind
    timestamp: datetime
    raw: Json
    meta: Optional[Mapping[str, str]] = None


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
