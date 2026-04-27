from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    data_mode: str
    database_url: str


def get_settings() -> Settings:
    return Settings(
        data_mode=os.getenv("DATA_MODE", "seeded"),
        database_url=os.getenv(
            "DATABASE_URL",
            "sqlite:///./altdata.db",
        ),
    )
