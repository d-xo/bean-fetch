from dataclasses import dataclass
from typing import List, Mapping

from bean_fetch.data import RawTx


@dataclass(frozen=True)
class Config:
    api_key: str
    api_secret: str
    account_prefix: str
    payment_methods: List[Mapping[str, str]]


def fetch(config: Config) -> List[RawTx]:
    return []
