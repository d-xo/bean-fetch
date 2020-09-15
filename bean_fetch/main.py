from datetime import datetime
import json
import hashlib
import argparse
from pathlib import Path
from typing import List, Any, Optional

import yaml
from pydantic.dataclasses import dataclass

from bean_fetch.data import RawTx, Kind
import bean_fetch.venues.coinbase as cb
import bean_fetch.venues.coinbasepro.venue as cbpro
import bean_fetch.venues.ethereum as eth


# --- constants ---

TIME_FORMAT = '%Y-%m-%dT%H:%M:%S.%f'

# --- cli ---

use = '''bean-fetch -c <CONFIG> <command>

The following commands are available
   fetch     Fetch raw transaction data from the outside world and persist it to disk
   parse     Parse the raw data into a beancount ledger
'''

parser = argparse.ArgumentParser(description="Fully automated command line bookkeeping", usage=use)
parser.add_argument("-c", "--config", required=True, help="configuration file path")
parser.add_argument("command", help="command to run")
args = parser.parse_args()


# --- config ---


@dataclass(frozen=True)
class Config:
    archive_dir: Path
    coinbase: Optional[cb.Config]
    coinbasepro: Optional[cbpro.Config]
    ethereum: Optional[eth.Config]


def load_config(path: Path) -> Config:
    config = yaml.load(path.read_text(), yaml.Loader)
    return Config(
        archive_dir=path.absolute().parent / config["archive_dir"],
        coinbase=cb.Config(**config["coinbase"]) if "coinbase" in config else None,
        coinbasepro=cbpro.Config(**config["coinbasepro"])
        if "coinbasepro" in config
        else None,
        ethereum=eth.Config(**config["ethereum"]) if "ethereum" in config else None,
    )


# --- archive ---


def serialize(path: Path, tx: RawTx[Kind]) -> None:
    """writes `tx` to `dir`. includes the sha256 hash of the contents in the filename"""
    time = tx.timestamp.strftime("%Y-%m-%d_%H-%M-%S")
    hash = hashlib.sha256(tx.to_json().encode('UTF-8')).hexdigest()
    out = tx.to_json(indent=4)
    path.mkdir(parents=True, exist_ok=True)
    (path / f"{tx.venue}-{tx.kind}-{time}-{hash}.json").write_text(out)


def deserialize(path: Path) -> RawTx[Kind]:
    j = json.loads(path.read_text())

    if j["venue"] == cb.VENUE:
        j["kind"] = cb.Kind(j["kind"])
    elif j["venue"] == cbpro.VENUE:
        j["kind"] = cbpro.Kind(j["kind"])
    elif j["venue"] == eth.VENUE:
        j["kind"] = eth.Kind(j["kind"])
    else:
        raise ValueError(f"unknown venue: {j['venue']}")

    return RawTx(
        kind=j["kind"],
        venue=j["venue"],
        timestamp=datetime.utcfromtimestamp(j["timestamp"]),
        raw=json.dumps(j["raw"])
    )


# --- main ---


def fetch(config: Config) -> None:
    raw: List[RawTx[Any]] = []

    if config.coinbase:
        print("fetching data from coinbase")
        raw += cb.Venue.fetch(config.coinbase)
    if config.coinbasepro:
        print("fetching data from coinbase pro")
        raw += cbpro.Venue.fetch(config.coinbasepro)
    if config.ethereum:
        print("fetching data from ethereum")
        raw += eth.Venue.fetch(config.ethereum)

    print("writing raw transaction data to archive")
    for tx in raw:
        serialize(config.archive_dir, tx)


def parse(config: Config) -> None:
    txs: List[RawTx[Any]] = [deserialize(p) for p in config.archive_dir.iterdir() if p.is_file()]

    for tx in txs:
        if cb.Venue.handles(tx) and config.coinbase:
            cb.Venue.parse(config.coinbase, tx)
        elif cbpro.Venue.handles(tx) and config.coinbasepro:
            cbpro.Venue.parse(config.coinbasepro, tx)
        elif eth.Venue.handles(tx) and config.ethereum:
            eth.Venue.parse(config.ethereum, tx)
        else:
            raise ValueError(f"unable to parse tx:\n {tx}")


def main() -> None:
    config = load_config(Path(args.config))

    if args.command == "fetch":
        fetch(config)
    elif args.command == "parse":
        parse(config)


if __name__ == "__main__":
    main()
