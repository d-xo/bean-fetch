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


# --- cli ---


parser = argparse.ArgumentParser(description="Fully automated command line bookkeeping")
parser.add_argument("-c", "--config", required=True, help="configuration file path")
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
        coinbasepro=cbpro.Config(**config["coinbasepro"]) if "coinbasepro" in config else None,
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
    return json.dumps(clean(obj), indent=4, ensure_ascii=False, sort_keys=True)


def soul(tx: RawTx[Enum]) -> str:
    """returns the sha256 hash of the serialized representation of `tx`"""
    return hashlib.sha256(dump(tx).encode("utf-8")).hexdigest()


def archive(path: Path, tx: RawTx[Enum]) -> None:
    """writes `tx` to `dir`. includes the sha256 hash of the contents in the filename"""
    path.mkdir(parents=True, exist_ok=True)
    (path / f"{tx.venue}-{tx.kind}-{tx.timestamp}-{soul(tx)}.json").write_text(dump(tx))


# --- main ---


def main() -> None:
    config = load_config(Path(args.config))

    raw: List[RawTx[Any]] = []

    if config.coinbase:
        raw += cb.Venue.fetch(config.coinbase)
    if config.coinbasepro:
        raw += cbpro.Venue.fetch(config.coinbasepro)
    if config.ethereum:
        raw += eth.Venue.fetch(config.ethereum)

    print(raw)

    for tx in raw:
        archive(config.archive_dir, tx)
