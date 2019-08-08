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

from bean_fetch.data import RawTx, VenueLike
from .data import Config, Kind, VENUE, Product, Account, Fill
from .client import Client

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
