from enum import Enum
from typing import List

from beancount.core.data import Transaction
from pydantic.dataclasses import dataclass

from bean_fetch.data import RawTx, VenueLike

# --- config ---


@dataclass(frozen=True)
class Config:
    rpc_url: str


# --- dispatch ---


VENUE = "ethereum"


class Kind(str, Enum):
    TRANSACTION = "transaction"


# --- venue ---


Raw = RawTx[Kind]


class Venue(VenueLike[Config, Kind]):
    @staticmethod
    def fetch(config: Config) -> List[Raw]:
        return []

    @staticmethod
    def handles(tx: Raw) -> bool:
        return tx.venue == VENUE and isinstance(tx.kind, Kind)

    @staticmethod
    def parse(config: Config, tx: Raw) -> Transaction:
        pass
