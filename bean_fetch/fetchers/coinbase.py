from dataclasses import dataclass
from typing import List, Mapping

from bean_fetch.data import RawTx, Globals


@dataclass(frozen=True)
class Config:
    api_key: str
    api_secret: str
    account_prefix: str
    fee_account: str
    payment_methods: List[Mapping[str, str]]


def buys() -> List[RawTx]:
    return []


def sells() -> List[RawTx]:
    return []


def deposits() -> List[RawTx]:
    return []


def withdrawals() -> List[RawTx]:
    return []


def fetch(globals: Globals, config: Config) -> List[RawTx]:
    return buys() + sells() + deposits() + withdrawals()
