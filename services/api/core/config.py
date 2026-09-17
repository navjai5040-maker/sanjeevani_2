from __future__ import annotations

import os
from functools import lru_cache


class Settings:
    def __init__(self) -> None:
        self.app_name = os.getenv('APP_NAME', 'Sanjeevani API')
        self.env = os.getenv('APP_ENV', 'development')
        self.database_url = os.getenv(
            'DATABASE_URL',
            'postgresql://sanjeevani:sanjeevani@localhost:5432/sanjeevani',
        )
        self.redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        self.jwt_secret = os.getenv('JWT_SECRET', 'change-me-in-production')


@lru_cache

def get_settings() -> Settings:
    return Settings()
