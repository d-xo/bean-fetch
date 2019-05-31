from dataclasses import field
from typing import List, Mapping, Optional, Iterable, Tuple, Callable, Any, Type, cast
from itertools import chain
from enum import Enum
from pathlib import Path
import json

import yaml
from pydantic.dataclasses import dataclass
from beancount.core.data import Transaction
from coinbase.wallet.client import Client
import coinbase.wallet.model as cb

from bean_fetch.data import RawTx, VenueLike


# --- constants ---


VENUE = "coinbase"


class Kind(str, Enum):
    BUY = "buy"
    SELL = "sell"
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"


# --- config ---


@dataclass(frozen=True)
class Config:
    api_key: str
    api_secret: str
    assets_prefix: str
    expenses_prefix: str
    payment_methods: Mapping[str, str]


# --- venue ---

Raw = RawTx[Kind]


class Venue(VenueLike[Config, Kind]):
    @staticmethod
    def fetch(config: Config) -> List[Raw]:
        client = Client(config.api_key, config.api_secret)
        accounts = client.get_accounts().data

        return list(
            Fetch.buys(accounts)
            + Fetch.sells(accounts)
            + Fetch.deposits(accounts)
            + Fetch.withdrawals(accounts)
        )

    @staticmethod
    def handles(tx: Raw) -> bool:
        return tx.venue == VENUE and isinstance(tx.kind, Kind)

    @staticmethod
    def parse(config: Config, tx: Raw) -> Transaction:
        assert Venue.handles(tx), "unparseable tx"

        dispatcher = {
            Kind.BUY: Parse.buy,
            Kind.SELL: Parse.sell,
            Kind.DEPOSIT: Parse.deposit,
            Kind.WITHDRAWAL: Parse.withdrawal,
        }

        return dispatcher[cast(Kind, tx.kind)](tx)


# --- fetcher ---


class Fetch:
    @staticmethod
    def buys(accounts: List[cb.Account]) -> List[Raw]:
        out: List[Raw] = []
        for acct in accounts:
            out += Fetch.transform(acct.get_buys().data, acct, Kind.BUY)
        return out

    @staticmethod
    def sells(accounts: List[cb.Account]) -> List[Raw]:
        out: List[Raw] = []
        for acct in accounts:
            out += Fetch.transform(acct.get_sells().data, acct, Kind.SELL)
        return out

    @staticmethod
    def deposits(accounts: List[cb.Account]) -> List[Raw]:
        out: List[Raw] = []
        for acct in accounts:
            out += Fetch.transform(acct.get_deposits().data, acct, Kind.DEPOSIT)
        return out

    @staticmethod
    def withdrawals(accounts: List[cb.Account]) -> List[Raw]:
        out: List[Raw] = []
        for acct in accounts:
            out += Fetch.transform(acct.get_withdrawals().data, acct, Kind.WITHDRAWAL)
        return out

    @staticmethod
    def transform(objs: List[cb.APIObject], acct: cb.Account, kind: Kind) -> List[Raw]:
        txs = []
        for obj in objs:
            txs.append(
                RawTx(
                    venue=VENUE,
                    kind=kind,
                    timestamp=obj.created_at,
                    meta={"account_id": acct.id},
                    raw=json.loads(str(obj)),
                )
            )
        return txs


# --- parser ---


class Parse:
    @staticmethod
    def buy(tx: Raw) -> Transaction:
        pass

    @staticmethod
    def sell(tx: Raw) -> Transaction:
        pass

    @staticmethod
    def deposit(tx: Raw) -> Transaction:
        pass

    @staticmethod
    def withdrawal(tx: Raw) -> Transaction:
        pass
