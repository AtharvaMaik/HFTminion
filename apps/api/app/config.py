from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    data_mode: str
    database_url: str
    live_vendor_feed_id: str
    live_vendor_symbol: str
    live_vendor_base_url: str
    live_refresh_window_seconds: int
    live_vendor_timeout_seconds: float


def get_settings() -> Settings:
    from .services.live_registry import LIVE_FEED_IDS

    default_database_url = "sqlite:////tmp/altdata.db" if os.getenv("VERCEL") else "sqlite:///./altdata.db"
    return Settings(
        data_mode=os.getenv("DATA_MODE", "seeded"),
        database_url=os.getenv(
            "DATABASE_URL",
            default_database_url,
        ),
        live_vendor_feed_id=os.getenv("LIVE_VENDOR_FEED_ID", LIVE_FEED_IDS[0]),
        live_vendor_symbol=os.getenv("LIVE_VENDOR_SYMBOL", "BTCUSDT"),
        live_vendor_base_url=os.getenv("LIVE_VENDOR_BASE_URL", "https://api.binance.us"),
        live_refresh_window_seconds=int(os.getenv("LIVE_REFRESH_WINDOW_SECONDS", "30")),
        live_vendor_timeout_seconds=float(os.getenv("LIVE_VENDOR_TIMEOUT_SECONDS", "5")),
    )
