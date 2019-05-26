import yaml
import argparse
from typing import List, Mapping, Optional
from pathlib import Path
from dataclasses import dataclass


parser = argparse.ArgumentParser(description="Fully automated command line bookkeeping")
parser.add_argument("-c", "--config", required=True, help="configuration file path")
args = parser.parse_args()


@dataclass(frozen=True)
class CoinbaseConfig:
    api_key: str
    api_secret: str
    account_prefix: str
    payment_methods: List[Mapping[str, str]]


@dataclass(frozen=True)
class Config:
    config_file: Path
    archive_dir: Path
    coinbase: Optional[CoinbaseConfig] = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "archive_dir", self.config_file.parent.joinpath(self.archive_dir)
        )


def load_config(path: Path) -> Config:
    return Config(config_file=path, **yaml.load(path.read_text(), yaml.Loader))


def main() -> None:
    config = load_config(Path(args.config))
    print(config)
