import yaml
import argparse
from pathlib import Path

parser = argparse.ArgumentParser(description="Fully automated command line bookkeeping")
parser.add_argument("-c", "--config", help="configuration file path")
args = parser.parse_args()


def main() -> None:
    print(args.config)
