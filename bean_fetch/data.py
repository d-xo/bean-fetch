from dataclasses import dataclass
from typing import Mapping, Any
from pathlib import Path
from abc import ABC


@dataclass(frozen=True)
class Globals:
    archive_dir: Path
    base_currency: str


@dataclass(frozen=True)
class RawTx:
    tag: str
    meta: Mapping[str, str]
    raw: Mapping[str, Any]
