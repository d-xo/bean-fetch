from enum import Enum
from datetime import datetime

from pydantic.dataclasses import dataclass
from beancount.core.amount import Decimal

# --- config ---


@dataclass(frozen=True)
class Config:
    api_key: str
    api_secret: str
    api_passphrase: str

# --- dispatch ---


VENUE = "coinbasepro"


class Kind(str, Enum):
    FILL = "fill"
    DEPOSIT = "deposit"
    WITHDRAW = "withdraw"


# --- api data ---


@dataclass(frozen=True)
class Product:
    """https://docs.pro.coinbase.com/#products"""

    id: str
    base_currency: str
    quote_currency: str
    base_min_size: Decimal
    base_max_size: Decimal
    base_increment: Decimal
    quote_increment: Decimal
    display_name: str
    status: str
    margin_enabled: bool
    status_message: str
    min_market_funds: Decimal
    max_market_funds: Decimal
    post_only: bool
    limit_only: bool
    cancel_only: bool
    trading_disabled: bool
    accessible: bool = False


@dataclass(frozen=True)
class Account:
    """https://docs.pro.coinbase.com/#accounts"""

    id: str
    currency: str
    balance: Decimal
    available: Decimal
    hold: Decimal
    profile_id: str
    trading_enabled: bool


@dataclass(frozen=True)
class Fill:
    """https://docs.pro.coinbase.com/#fills"""

    trade_id: int
    product_id: str
    price: Decimal
    size: Decimal
    order_id: str
    created_at: datetime
    user_id: str
    profile_id: str
    liquidity: str
    fee: Decimal
    side: str
    settled: bool
    usd_volume: str
