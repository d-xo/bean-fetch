import json
import hashlib
import argparse
from pathlib import Path
from dataclasses import dataclass
from typing import List, Mapping, Optional, Any

import yaml

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


# --- archives ---


def archive(root: Path, tx: RawTx) -> None:
    content_hash = hashlib.sha256(json.dumps(tx.raw).encode("utf-8")).hexdigest()
    file = root / f"{tx.venue}-{tx.kind}-{tx.timestamp}-{content_hash}.json"
    file.write_text(json.dumps(tx.__dict__, indent=4))


# --- main ---


def main() -> None:
    config = load_config(Path(args.config))

    raw: List[RawTx] = []
    # raw += coinbase.Venue.fetch(config.coinbase)
    raw += coinbasepro.Venue.fetch(config.coinbasepro)

    for tx in raw:
        archive(config.archive_dir, tx)
