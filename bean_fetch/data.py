from dataclasses import dataclass
from typing import Mapping, Any, Optional
from pathlib import Path
from enum import Enum


@dataclass(frozen=True)
class Globals:
    archive_dir: Path
    base_currency: str


@dataclass(frozen=True)
class Tag:
    venue: str
    kind: Enum


@dataclass(frozen=True)
class RawTx:
    tag: Tag
    raw: Mapping[str, Any]
    meta: Optional[Mapping[str, str]] = None
