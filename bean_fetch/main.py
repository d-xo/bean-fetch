import yaml
import argparse
from typing import List, Mapping, Optional, Any
from pathlib import Path
from dataclasses import dataclass

import bean_fetch.fetchers.coinbase as coinbase
from bean_fetch.data import RawTx, Globals


# --- cli ---


parser = argparse.ArgumentParser(description="Fully automated command line bookkeeping")
parser.add_argument("-c", "--config", required=True, help="configuration file path")
args = parser.parse_args()


# --- config ---


@dataclass(frozen=True)
class Config:
    globals: Globals
    coinbase: coinbase.Config


def load_config(path: Path) -> Config:
    config = yaml.load(path.read_text(), yaml.Loader)

    # make relative paths absolute
    config["globals"]["archive_dir"] = (
        path.absolute().parent / config["globals"]["archive_dir"]
    )

    return Config(**config)


# --- main ---


def main() -> None:
    config = load_config(Path(args.config))

    raw: List[RawTx] = []
    raw += coinbase.fetch(config.globals, config.coinbase)

    print(raw)
    print(config)
