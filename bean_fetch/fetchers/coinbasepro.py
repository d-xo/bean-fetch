import json
import jsonpickle
import functools
import operator
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Mapping, Iterator, Any
from datetime import datetime

from pydantic.dataclasses import dataclass
from beancount.core.data import Transaction
from beancount.core.amount import Decimal
from cbpro import AuthenticatedClient as Client

from bean_fetch.data import RawTx, VenueLike


# --- config ---


@dataclass(frozen=True)
class Config:
    api_key: str
    api_secret: str
    api_passphrase: str
    assets_prefix: str
    expenses_prefix: str
    payment_methods: Mapping[str, str]


# --- dispatch ---


VENUE = "coinbasepro"


class Kind(str, Enum):
    FILL = "fill"
    DEPOSIT = "deposit"
    WITHDRAW = "withdraw"


# --- venue ---

Raw = RawTx[Kind]


class Venue(VenueLike[Config, Kind]):
    @staticmethod
    def fetch(config: Config) -> List[Raw]:
        client = Client(config.api_key, config.api_secret, config.api_passphrase)
        products = [Product(**p) for p in client.get_products()]
        accounts = [Account(**a) for a in client.get_accounts()]
        return Fetch.fills(client, products) + Fetch.transfers(client, accounts)

    @staticmethod
    def handles(tx: Raw) -> bool:
        return tx.venue == VENUE and isinstance(tx.kind, Kind)

    @staticmethod
    def parse(config: Config, tx: Raw) -> Transaction:
        pass


# --- api data ---


@dataclass(frozen=True)
class Product:
    """https://docs.pro.coinbase.com/#products"""

    id: str
    base_currency: str
    quote_currency: str
    base_min_size: Decimal
    base_max_size: Decimal
    base_increment: Decimal
    quote_increment: Decimal
    display_name: str
    status: str
    margin_enabled: bool
    status_message: str
    min_market_funds: Decimal
    max_market_funds: Decimal
    post_only: bool
    limit_only: bool
    cancel_only: bool
    accessible: bool = False


@dataclass(frozen=True)
class Account:
    """https://docs.pro.coinbase.com/#accounts"""

    id: str
    currency: str
    balance: Decimal
    available: Decimal
    hold: Decimal
    profile_id: str


@dataclass(frozen=True)
class Fill:
    """https://docs.pro.coinbase.com/#fills"""

    trade_id: int
    product_id: str
    price: Decimal
    size: Decimal
    order_id: str
    created_at: datetime
    user_id: str
    profile_id: str
    liquidity: str
    fee: Decimal
    side: str
    settled: bool
    usd_volume: str


# --- fetcher ---


class Fetch:
    @staticmethod
    def fills(client: Client, products: List[Product]) -> List[Raw]:
        out: List[Raw] = []
        for p in products:
            fs = [Fill(**f) for f in client.get_fills(product_id=p.id)]
            out += [
                Raw(
                    venue=VENUE,
                    kind=Kind.FILL,
                    timestamp=str(f.created_at),
                    raw=jsonpickle.encode(f, unpicklable=False),
                    meta=None,
                )
                for f in fs
            ]
        return out

    @staticmethod
    def transfers(c: Client, accounts: List[Account]) -> List[Raw]:
        out: List[Raw] = []
        for a in accounts:
            transfers = [
                x for x in c.get_account_history(a.id) if x["type"] == "transfer"
            ]
            out += [
                Raw(
                    venue=VENUE,
                    kind=Kind(t["details"]["transfer_type"]),
                    timestamp=t["created_at"],
                    raw=jsonpickle.encode(t, unpicklable=False),
                    meta={"account_id": a.id, "currency": a.currency},
                )
                for t in transfers
            ]
        return out
