from dataclasses import dataclass, field
from typing import List, Mapping, Optional, Iterable, Tuple, Callable, Any, Type, cast
from itertools import chain
from enum import Enum
from pathlib import Path
import json

import yaml
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
    payment_methods: List[Mapping[str, str]]


# --- venue ---


class Venue(VenueLike[Config]):
    @staticmethod
    def fetch(config: Config) -> List[RawTx]:
        client = Client(config.api_key, config.api_secret)
        accounts = client.get_accounts().data

        return list(
            Fetch.buys(accounts)
            + Fetch.sells(accounts)
            + Fetch.deposits(accounts)
            + Fetch.withdrawals(accounts)
        )

    @staticmethod
    def handles(tx: RawTx) -> bool:
        return tx.venue == VENUE and isinstance(tx.kind, Kind)

    @staticmethod
    def parse(config: Config, tx: RawTx) -> Transaction:
        assert Venue.handles(tx), "unknown tx kind"

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
    def buys(accounts: List[cb.Account]) -> List[RawTx]:
        out: List[RawTx] = []
        for acct in accounts:
            out += Fetch.transform(acct.get_buys().data, acct, Kind.BUY)
        return out

    @staticmethod
    def sells(accounts: List[cb.Account]) -> List[RawTx]:
        out: List[RawTx] = []
        for acct in accounts:
            out += Fetch.transform(acct.get_sells().data, acct, Kind.SELL)
        return out

    @staticmethod
    def deposits(accounts: List[cb.Account]) -> List[RawTx]:
        out: List[RawTx] = []
        for acct in accounts:
            out += Fetch.transform(acct.get_deposits().data, acct, Kind.DEPOSIT)
        return out

    @staticmethod
    def withdrawals(accounts: List[cb.Account]) -> List[RawTx]:
        out: List[RawTx] = []
        for acct in accounts:
            out += Fetch.transform(acct.get_withdrawals().data, acct, Kind.WITHDRAWAL)
        return out

    @staticmethod
    def transform(
        objs: List[cb.APIObject], acct: cb.Account, kind: Kind
    ) -> List[RawTx]:
        txs = []
        for obj in objs:
            txs.append(
                RawTx(
                    venue=VENUE,
                    kind=kind,
                    timestamp=obj.created_at,
                    meta={"account_id": acct.id},
                    raw=str(obj),
                )
            )
        return txs


# --- parser ---


class Parse:
    @staticmethod
    def buy(tx: RawTx) -> Transaction:
        pass

    @staticmethod
    def sell(tx: RawTx) -> Transaction:
        pass

    @staticmethod
    def deposit(tx: RawTx) -> Transaction:
        pass

    @staticmethod
    def withdrawal(tx: RawTx) -> Transaction:
        pass
