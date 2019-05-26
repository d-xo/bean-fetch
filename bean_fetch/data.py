@dataclass(frozen=True)
class RawTx:
    tag: str
    meta: Mapping[str, str]
    raw: Mapping[str, Any]
