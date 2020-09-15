from datetime import datetime
from enum import Enum
from typing import List, Optional

from beancount.core.data import Transaction
from dataclasses_json import dataclass_json
from eth_typing import ChecksumAddress
from pydantic.dataclasses import dataclass
from web3 import Web3
from web3.middleware import geth_poa_middleware

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
    TRANSACTION = "TRANSACTION"


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
            block = web3.eth.getBlock(i, full_transactions=True)
            for tx in block.transactions:
                if (tx["from"] in config.addresses) or (tx["to"] in config.addresses):
                    receipt = web3.eth.getTransactionReceipt(tx.hash)
                    transactions.append(
                        EthTx(
                            timestamp=datetime.utcfromtimestamp(block.timestamp),
                            blockHash=tx.blockHash.hex(),
                            blockNumber=tx.blockNumber,
                            chainId=tx.chainId if "chainId" in tx else 1,
                            data=tx.data if "data" in tx else None,
                            sender=tx["from"],
                            receiver=tx.to if tx.to else None,
                            gas=tx.gas,
                            gasPrice=tx.gasPrice,
                            hash=tx.hash.hex(),
                            input=tx.input,
                            nonce=tx.nonce,
                            value=tx.value,
                            receipt=TxReceipt(
                                contractAddress=receipt.contractAddress,
                                cumulativeGasUsed=receipt.cumulativeGasUsed,
                                gasUsed=receipt.gasUsed,
                                logs=[
                                    LogReceipt(
                                        address=log.address,
                                        data=log.data,
                                        logIndex=log.logIndex,
                                        payload=log.payload.hex() if "payload" in log else None,
                                        removed=log.removed,
                                        topic=log.topic.hex() if "topic" in log else None,
                                        topics=[t.hex() for t in log.topics],
                                    ) for log in receipt.logs
                                ],
                                logsBloom=str(receipt.logsBloom),
                                root=receipt.root.hex() if "root" in receipt else None,
                                status=receipt.status,
                            ),
                        ))

        return [
            RawTx(venue=VENUE,
                  kind=Kind.TRANSACTION,
                  timestamp=t.timestamp,
                  raw=t.to_json(),
                  meta={}) for t in transactions
        ]

    @staticmethod
    def handles(tx: Raw) -> bool:
        return tx.venue == VENUE and isinstance(tx.kind, Kind)

    @staticmethod
    def parse(config: Config, raw: Raw) -> Transaction:
        tx = EthTx(**raw.raw)
        print(tx)


# --- data ---


@dataclass_json
@dataclass(frozen=True)
class LogReceipt:
    address: ChecksumAddress
    data: str
    logIndex: int
    payload: Optional[str]
    removed: bool
    topic: Optional[str]
    topics: List[str]


@dataclass_json
@dataclass(frozen=True)
class TxReceipt:
    contractAddress: Optional[ChecksumAddress]
    cumulativeGasUsed: int
    gasUsed: int
    logs: List[LogReceipt]
    logsBloom: str
    root: Optional[str]
    status: int


@dataclass_json
@dataclass(frozen=True)
class EthTx:
    timestamp: datetime
    blockHash: str
    blockNumber: int
    chainId: int
    data: Optional[bytes]
    sender: ChecksumAddress
    receiver: Optional[ChecksumAddress]
    gas: int
    gasPrice: int
    hash: str
    input: str
    nonce: int
    value: int
    receipt: TxReceipt
