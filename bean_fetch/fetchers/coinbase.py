from dataclasses import dataclass, field
from typing import List, Mapping, Optional, Iterable, Tuple
import json

from coinbase.wallet.client import Client
import coinbase.wallet.model as model

from bean_fetch.data import RawTx, Globals, Tag

# --- utils ---


def transform(
    objs: List[model.APIObject], acct: model.Account, kind: str
) -> List[RawTx]:
    return list(
        map(
            lambda obj: RawTx(
                tag=Tag(venue="coinbase", kind=kind),
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


@dataclass
class Fetcher:
    globals: Globals
    config: Config

    client: Client = None
    accounts: Iterable[model.Account] = ()

    def __post_init__(self) -> None:
        self.client = Client(self.config.api_key, self.config.api_secret)
        self.accounts = tuple(self.client.get_accounts().data)

    def all(self) -> List[RawTx]:
        return self.buys() + self.sells() + self.deposits() + self.withdrawals()

    def buys(self) -> List[RawTx]:
        out: List[RawTx] = []
        for acct in self.accounts:
            out += transform(acct.get_buys().data, acct, "buy")
        return out

    def sells(self) -> List[RawTx]:
        out: List[RawTx] = []
        for acct in self.accounts:
            out += transform(acct.get_sells().data, acct, "sell")
        return out

    def deposits(self) -> List[RawTx]:
        out: List[RawTx] = []
        for acct in self.accounts:
            out += transform(acct.get_deposits().data, acct, "deposit")
        return out

    def withdrawals(self) -> List[RawTx]:
        out: List[RawTx] = []
        for acct in self.accounts:
            out += transform(acct.get_withdrawals().data, acct, "withdrawal")
        return out
