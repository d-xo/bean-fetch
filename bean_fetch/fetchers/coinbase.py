from dataclasses import dataclass, field
from typing import List, Mapping, Optional, Iterable, Tuple, Callable, Any, Type
from itertools import chain
from enum import Enum
import json

from beancount.core.data import Transaction
from coinbase.wallet.client import Client
import coinbase.wallet.model as cb

from bean_fetch.data import RawTx, Globals, Tag, Venue


# --- constants ---


VENUE = "coinbase"


class Kind(Enum):
    BUY = "buy"
    SELL = "sell"
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"


# --- config ---


@dataclass(frozen=True)
class CoinbaseConfig:
    api_key: str
    api_secret: str
    assets_prefix: str
    expenses_prefix: str
    payment_methods: List[Mapping[str, str]]


# --- venue ---


class Coinbase(Venue[CoinbaseConfig]):
    @staticmethod
    def fetch(config: CoinbaseConfig) -> List[RawTx]:
        client = Client(config.api_key, config.api_secret)
        accounts = client.get_accounts().data

        return list(
            Fetch.buys(accounts)
            + Fetch.sells(accounts)
            + Fetch.deposits(accounts)
            + Fetch.withdrawals(accounts)
        )

    @staticmethod
    def handles(tag: Tag) -> bool:
        return tag.venue == VENUE and tag.kind is Kind

    @staticmethod
    def parse(config: CoinbaseConfig, tx: RawTx) -> Transaction:
        assert tx.tag.venue == VENUE, "unknown venue"

        dispatcher = {
            Kind.BUY: Parse.buy,
            Kind.SELL: Parse.sell,
            Kind.DEPOSIT: Parse.deposit,
            Kind.WITHDRAWAL: Parse.withdrawal,
        }

        kind = Kind(tx.tag)
        return dispatcher[kind](tx)


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
                    tag=Tag(venue=VENUE, kind=kind),
                    meta={"account_id": acct.id},
                    raw=json.loads(str(obj)),
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
