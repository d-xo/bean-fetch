from datetime import datetime
from enum import Enum
from typing import List

import jsonpickle
from web3 import Web3
from web3.middleware import geth_poa_middleware
from eth_typing import ChecksumAddress
from beancount.core.data import Transaction
from pydantic.dataclasses import dataclass

from bean_fetch.data import RawTx, VenueLike

# --- config ---


@dataclass(frozen=True)
class Config:
    rpc_url: str
    addresses: List[ChecksumAddress]
    start_block: int


# --- dispatch ---


VENUE = "ethereum"


class Kind(str, Enum):
    TRANSACTION = "transaction"


# --- venue ---


Raw = RawTx[Kind]


class Venue(VenueLike[Config, Kind]):
    @staticmethod
    def fetch(config: Config) -> List[Raw]:
        web3 = Web3(Web3.HTTPProvider(config.rpc_url))
        web3.middleware_onion.inject(geth_poa_middleware, layer=0)
        web3.enable_strict_bytes_type_checking()

        blockheight = web3.eth.getBlock('latest').number

        transactions = []
        for i in range(config.start_block, blockheight + 1):
            txs = web3.eth.getBlock(i, full_transactions=True).transactions
            for tx in txs:
                if (tx["from"] in config.addresses) or (tx["to"] in config.addresses):
                    block = web3.eth.getBlock(i)
                    txHash = block.transactions[tx.transactionIndex]
                    timestamp = block.timestamp
                    transactions.append((tx, txHash, timestamp))

        return [RawTx(
            venue="Ethereum",
            kind=Kind.TRANSACTION,
            timestamp=datetime.utcfromtimestamp(timestamp),
            raw=jsonpickle.encode(tx),
            meta={"txHash": hash.hex()}
        ) for (t, hash, stamp) in transactions]

    @staticmethod
    def handles(tx: Raw) -> bool:
        return tx.venue == VENUE and isinstance(tx.kind, Kind)

    @staticmethod
    def parse(config: Config, tx: Raw) -> Transaction:
        pass
