import yaml
import argparse
from typing import List, Mapping
from pathlib import Path
from dataclasses import dataclass


parser = argparse.ArgumentParser(description="Fully automated command line bookkeeping")
parser.add_argument("-c", "--config", required=True, help="configuration file path")
args = parser.parse_args()


@dataclass
class CoinbaseConfig:
    api_key: str
    api_secret: str
    account_prefix: str
    payment_methods: List[Mapping[str, str]]


@dataclass
class Config:
    coinbase: CoinbaseConfig


def load_config(path: Path) -> Config:
    return Config(**yaml.load(path.read_text(), yaml.Loader))


def main() -> None:
    load_config(Path(args.config))
