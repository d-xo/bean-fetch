from dataclasses import dataclass, field
from typing import List, Mapping, Optional, Iterable, Tuple
from itertools import chain
from enum import Enum
import json

from coinbase.wallet.client import Client
from coinbase.wallet.model import Account, APIObject

from bean_fetch.data import RawTx, Globals, Tag


# --- constants ---


VENUE = "coinbase"


class Kind(Enum):
    BUY = "buy"
    SELL = "sell"
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"


# --- utils ---


def transform(objs: List[APIObject], acct: Account, kind: Kind) -> List[RawTx]:
    return list(
        map(
            lambda obj: RawTx(
                tag=Tag(venue=VENUE, kind=kind),
                meta={"account_id": acct.id},
                raw=json.loads(str(obj)),
            ),
            objs,
        )
    )


# --- config ---


@dataclass(frozen=True)
class Config:
    api_key: str
    api_secret: str
    assets_prefix: str
    expenses_prefix: str
    payment_methods: List[Mapping[str, str]]


# --- fetcher ---


class Fetcher:
    @staticmethod
    def fetch(config: Config) -> Iterable[RawTx]:
        client = Client(config.api_key, config.api_secret)
        accounts = client.get_accounts().data
        return chain(
            Fetcher._buys(accounts),
            Fetcher._sells(accounts),
            Fetcher._deposits(accounts),
            Fetcher._withdrawals(accounts),
        )

    @staticmethod
    def _buys(accounts: List[Account]) -> Iterable[RawTx]:
        out: List[RawTx] = []
        for acct in accounts:
            out += transform(acct.get_buys().data, acct, Kind.BUY)
        return tuple(out)

    @staticmethod
    def _sells(accounts: List[Account]) -> Iterable[RawTx]:
        out: List[RawTx] = []
        for acct in accounts:
            out += transform(acct.get_sells().data, acct, Kind.SELL)
        return tuple(out)

    @staticmethod
    def _deposits(accounts: List[Account]) -> Iterable[RawTx]:
        out: List[RawTx] = []
        for acct in accounts:
            out += transform(acct.get_deposits().data, acct, Kind.DEPOSIT)
        return tuple(out)

    @staticmethod
    def _withdrawals(accounts: List[Account]) -> Iterable[RawTx]:
        out: List[RawTx] = []
        for acct in accounts:
            out += transform(acct.get_deposits().data, acct, Kind.WITHDRAWAL)
        return tuple(out)
