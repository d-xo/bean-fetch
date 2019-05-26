import yaml
import argparse
from typing import List, Mapping, Optional, Any
from pathlib import Path
from dataclasses import dataclass

from bean_fetch.fetchers.coinbase import Coinbase, CoinbaseConfig
from bean_fetch.data import RawTx, Globals


# --- cli ---


parser = argparse.ArgumentParser(description="Fully automated command line bookkeeping")
parser.add_argument("-c", "--config", required=True, help="configuration file path")
args = parser.parse_args()


# --- config ---


@dataclass(frozen=True)
class Config:
    globals: Globals
    coinbase: CoinbaseConfig


def load_config(path: Path) -> Config:
    config = yaml.load(path.read_text(), yaml.Loader)

    # make relative paths absolute
    config["globals"]["archive_dir"] = (
        path.absolute().parent / config["globals"]["archive_dir"]
    )

    return Config(
        globals=Globals(**config["globals"]),
        coinbase=CoinbaseConfig(**config["coinbase"]),
    )


# --- main ---


def main() -> None:
    config = load_config(Path(args.config))

    raw: List[RawTx] = []
    raw += Coinbase.fetch(config.coinbase)

    print(raw)
