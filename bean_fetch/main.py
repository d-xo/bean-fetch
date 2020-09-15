from datetime import datetime
import json
import hashlib
import argparse
from enum import Enum
from pathlib import Path
from typing import List, Any, Dict, Optional

import yaml
import jsonpickle
from pydantic.dataclasses import dataclass
from bean_fetch.data import RawTx

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


def clean(d: Dict[str, Any]) -> Dict[str, Any]:
    """returns a copy of `d` with all dunder keys removed"""
    return {
        k: clean(v) if isinstance(v, Dict) else v
        for k, v in d.items()
        if not k.startswith("__")
    }


def dump(tx: RawTx[Enum]) -> str:
    """returns a pretty printed json representation of `tx`"""
    obj = json.loads(jsonpickle.encode(tx, unpicklable=False))
    obj["kind"] = tx.kind._name_
    obj["timestamp"] = tx.timestamp.strftime(TIME_FORMAT)
    return json.dumps(clean(obj), indent=4, ensure_ascii=False, sort_keys=True)


def soul(tx: RawTx[Enum]) -> str:
    """returns the sha256 hash of the serialized representation of `tx`"""
    return hashlib.sha256(dump(tx).encode("utf-8")).hexdigest()


def archive(path: Path, tx: RawTx[Enum]) -> None:
    """writes `tx` to `dir`. includes the sha256 hash of the contents in the filename"""
    time = tx.timestamp.strftime("%Y-%m-%d_%H-%M-%S")
    path.mkdir(parents=True, exist_ok=True)
    (path / f"{tx.venue}-{tx.kind}-{time}-{soul(tx)}.json").write_text(dump(tx))


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
        archive(config.archive_dir, tx)


def parse(config: Config) -> None:
    def mkRaw(j: Dict) -> RawTx:
        if j["venue"] == cb.VENUE:
            j["kind"] = cb.Kind(j["kind"])
        elif j["venue"] == cbpro.VENUE:
            j["kind"] = cbpro.Kind(j["kind"])
        elif j["venue"] == eth.VENUE:
            j["kind"] = eth.Kind(j["kind"])
        else:
            raise ValueError(f'unknown venue: {j["venue"]}')

        return RawTx(
            kind=j["kind"],
            venue=j["venue"],
            timestamp=datetime.strptime(j["timestamp"], TIME_FORMAT),
            raw=json.dumps(j["raw"])
        )
    raw = [mkRaw(json.loads(p.read_text())) for p in config.archive_dir.iterdir() if p.is_file()]

    for tx in raw:
        if cb.Venue.handles(tx):
            cb.Venue.parse(config.coinbase, tx)
        if cbpro.Venue.handles(tx):
            cbpro.Venue.parse(config.coinbasepro, tx)
        elif eth.Venue.handles(tx):
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
