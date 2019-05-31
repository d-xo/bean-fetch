import json
import hashlib
import argparse
from pathlib import Path
from typing import List, Mapping, Optional, Any, Dict

import yaml
import jsonpickle
from pydantic.dataclasses import dataclass
from bean_fetch.data import RawTx
import bean_fetch.fetchers.coinbase as coinbase
import bean_fetch.fetchers.coinbasepro as coinbasepro


# --- cli ---


parser = argparse.ArgumentParser(description="Fully automated command line bookkeeping")
parser.add_argument("-c", "--config", required=True, help="configuration file path")
args = parser.parse_args()


# --- config ---


@dataclass(frozen=True)
class Config:
    archive_dir: Path
    coinbase: coinbase.Config
    coinbasepro: coinbasepro.Config


def load_config(path: Path) -> Config:
    config = yaml.load(path.read_text(), yaml.Loader)
    return Config(
        archive_dir=path.absolute().parent / config["archive_dir"],
        coinbase=coinbase.Config(**config["coinbase"]),
        coinbasepro=coinbasepro.Config(**config["coinbasepro"]),
    )


# --- archive ---


def clean(d: Dict[str, Any]) -> Dict[str, Any]:
    """returns a copy of `d` with all dunder keys removed"""
    return {
        k: clean(v) if isinstance(v, Dict) else v
        for k, v in d.items()
        if not k.startswith("__")
    }


def dump(tx: RawTx[Any]) -> str:
    """returns a pretty printed json representation of `tx`"""
    obj = json.loads(jsonpickle.encode(tx, unpicklable=False))
    obj["kind"] = obj["kind"]["_name_"]
    return json.dumps(clean(obj), indent=4, ensure_ascii=False, sort_keys=True)


def soul(tx: RawTx[Any]) -> str:
    """returns the sha256 hash of `tx`"""
    return hashlib.sha256(dump(tx).encode("utf-8")).hexdigest()


def archive(path: Path, tx: RawTx[Any]) -> None:
    """writes `tx` to `dir`. includes the sha256 hash of the contents in the filename"""
    assert path.is_dir(), f"{path} is not a directory"
    (path / f"{tx.venue}-{tx.kind}-{tx.timestamp}-{soul(tx)}.json").write_text(dump(tx))


# --- main ---


def main() -> None:
    config = load_config(Path(args.config))

    raw: List[RawTx[Any]] = []
    # raw += coinbase.Venue.fetch(config.coinbase)
    raw += coinbasepro.Venue.fetch(config.coinbasepro)

    for tx in raw:
        archive(config.archive_dir, tx)
