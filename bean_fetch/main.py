import yaml
import argparse
from pathlib import Path

parser = argparse.ArgumentParser(description="Full automated command line bookkeeping")
parser.add_argument(
    "-c", "--config", default=Path.cwd(), help="configuration file path"
)
args = parser.parse_args()


def main():
    print("compile!")
