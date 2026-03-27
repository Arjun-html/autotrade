"""Parquet-backed local data cache with TTL and in-memory L1 layer.

Architecture:
  L1 — in-process Python dict (fast, lost on restart)
  L2 — parquet files on disk (survives restarts, survives across runs)

Cache keys encode symbol + timeframe + date range so different date ranges
for the same symbol are stored separately.  When a request is partially
covered by the cache the missing portion is fetched and merged.

Usage:
    from data.cache import DataCache
    from data.providers.alpaca import AlpacaDataProvider

    provider = AlpacaDataProvider(...)
    cache = DataCache(provider, cache_dir=Path("cache"), ttl_seconds=3600)

    df = cache.get_bars("AAPL", start, end)   # transparently hits L2 or provider
"""

from __future__ import annotations

import hashlib
import json
import logging
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

import pandas as pd

from .base import DataProvider
from .models import AssetClass, AssetInfo, Bar, Quote, Timeframe

logger = logging.getLogger(__name__)


def _utc_now() -> float:
    """Return current UTC time as a Unix timestamp."""
    return time.time()


def _cache_key(symbol: str, timeframe: Timeframe, start: datetime, end: datetime) -> str:
    """Build a deterministic, filesystem-safe cache key string."""
    raw = f"{symbol}|{timeframe.value}|{start.isoformat()}|{end.isoformat()}"
    digest = hashlib.sha256(raw.encode()).hexdigest()[:16]
    safe_symbol = symbol.replace("/", "-")
    return f"{safe_symbol}_{timeframe.value}_{digest}"


class DataCache(DataProvider):
    """A DataProvider that wraps another provider and caches results locally.

    Args:
        provider: The upstream DataProvider to fetch from on cache misses.
        cache_dir: Directory for parquet cache files.
        ttl_seconds: Seconds before a cache entry is considered stale.
        max_memory_entries: Maximum number of DataFrames held in the L1 dict.
    """

    def __init__(
        self,
        provider: DataProvider,
        cache_dir: Path = Path("cache"),
        ttl_seconds: int = 3600,
        max_memory_entries: int = 128,
    ) -> None:
        self._provider = provider
        self._cache_dir = Path(cache_dir)
        self._ttl = ttl_seconds
        self._max_memory = max_memory_entries

        self._memory: dict[str, tuple[pd.DataFrame, float]] = {}  # key → (df, stored_at)
        self._lock = threading.Lock()

        self._cache_dir.mkdir(parents=True, exist_ok=True)

    # ----------------------------------------------------------------- helpers

    def _meta_path(self, key: str) -> Path:
        return self._cache_dir / f"{key}.meta.json"

    def _data_path(self, key: str) -> Path:
        return self._cache_dir / f"{key}.parquet"

    def _is_fresh(self, stored_at: float) -> bool:
        return (_utc_now() - stored_at) < self._ttl

    def _read_l1(self, key: str) -> pd.DataFrame | None:
        with self._lock:
            entry = self._memory.get(key)
        if entry is None:
            return None
        df, stored_at = entry
        if self._is_fresh(stored_at):
            return df
        with self._lock:
            self._memory.pop(key, None)
        return None

    def _write_l1(self, key: str, df: pd.DataFrame) -> None:
        with self._lock:
            if len(self._memory) >= self._max_memory:
                # Evict the oldest entry (LRU approximation — evict min stored_at)
                oldest = min(self._memory, key=lambda k: self._memory[k][1])
                del self._memory[oldest]
            self._memory[key] = (df, _utc_now())

    def _read_l2(self, key: str) -> pd.DataFrame | None:
        meta_path = self._meta_path(key)
        data_path = self._data_path(key)
        if not meta_path.exists() or not data_path.exists():
            return None
        try:
            meta = json.loads(meta_path.read_text())
            stored_at: float = meta.get("stored_at", 0.0)
            if not self._is_fresh(stored_at):
                logger.debug("Cache stale for key=%s", key)
                return None
            df = pd.read_parquet(data_path)
            if not df.empty:
                df.index = pd.to_datetime(df.index, utc=True)
            return df
        except Exception:
            logger.warning("Failed to read cache key=%s", key, exc_info=True)
            return None

    def _write_l2(self, key: str, df: pd.DataFrame) -> None:
        try:
            meta = {"stored_at": _utc_now(), "rows": len(df)}
            self._meta_path(key).write_text(json.dumps(meta))
            df.to_parquet(self._data_path(key))
        except Exception:
            logger.warning("Failed to write cache key=%s", key, exc_info=True)

    def _get_cached(self, key: str) -> pd.DataFrame | None:
        df = self._read_l1(key)
        if df is not None:
            return df
        df = self._read_l2(key)
        if df is not None:
            self._write_l1(key, df)
        return df

    def _set_cached(self, key: str, df: pd.DataFrame) -> None:
        self._write_l1(key, df)
        self._write_l2(key, df)

    # ------------------------------------------------------ DataProvider impl

    def get_bars(
        self,
        symbol: str,
        start: datetime,
        end: datetime,
        timeframe: Timeframe = Timeframe.DAY_1,
        limit: int | None = None,
    ) -> pd.DataFrame:
        """Return cached bars or fetch from upstream provider on miss."""
        key = _cache_key(symbol, timeframe, start, end)
        cached = self._get_cached(key)
        if cached is not None:
            logger.debug("Cache hit: %s", key)
            return cached if limit is None else cached.iloc[:limit]

        logger.debug("Cache miss: %s — fetching from provider", key)
        df = self._provider.get_bars(symbol, start, end, timeframe, limit)
        if not df.empty:
            self._set_cached(key, df)
        return df

    def get_multi_bars(
        self,
        symbols: list[str],
        start: datetime,
        end: datetime,
        timeframe: Timeframe = Timeframe.DAY_1,
    ) -> dict[str, pd.DataFrame]:
        """Fetch multiple symbols, returning each from cache where possible."""
        result: dict[str, pd.DataFrame] = {}
        misses: list[str] = []

        for sym in symbols:
            key = _cache_key(sym, timeframe, start, end)
            cached = self._get_cached(key)
            if cached is not None:
                result[sym] = cached
            else:
                misses.append(sym)

        if misses:
            fetched = self._provider.get_multi_bars(misses, start, end, timeframe)
            for sym, df in fetched.items():
                if not df.empty:
                    key = _cache_key(sym, timeframe, start, end)
                    self._set_cached(key, df)
                result[sym] = df

        return result

    def get_latest_bar(self, symbol: str) -> Bar | None:
        """Latest bars are always fetched live (not cached)."""
        return self._provider.get_latest_bar(symbol)

    def get_latest_bars(self, symbols: list[str]) -> dict[str, Bar | None]:
        return self._provider.get_latest_bars(symbols)

    def get_latest_quote(self, symbol: str) -> Quote | None:
        return self._provider.get_latest_quote(symbol)

    def get_assets(
        self,
        asset_class: AssetClass = AssetClass.US_EQUITY,
        tradable_only: bool = True,
    ) -> list[AssetInfo]:
        """Asset lists are cached with a longer TTL (treated as 24h by using a fixed key)."""
        key = f"assets_{asset_class.value}_tradable{tradable_only}"
        cache_path = self._cache_dir / f"{key}.json"
        meta_path = self._cache_dir / f"{key}.meta.json"

        if meta_path.exists() and cache_path.exists():
            try:
                meta = json.loads(meta_path.read_text())
                if self._is_fresh(meta.get("stored_at", 0)):
                    raw = json.loads(cache_path.read_text())
                    return [AssetInfo(**a) for a in raw]
            except Exception:
                pass

        assets = self._provider.get_assets(asset_class, tradable_only)
        try:
            cache_path.write_text(json.dumps([a.model_dump() for a in assets]))
            meta_path.write_text(json.dumps({"stored_at": _utc_now()}))
        except Exception:
            pass
        return assets

    def get_asset(self, symbol: str) -> AssetInfo | None:
        return self._provider.get_asset(symbol)

    def subscribe_bars(
        self,
        symbols: list[str],
        callback: Callable[[Bar], None],
    ) -> None:
        self._provider.subscribe_bars(symbols, callback)

    def subscribe_quotes(
        self,
        symbols: list[str],
        callback: Callable[[Quote], None],
    ) -> None:
        self._provider.subscribe_quotes(symbols, callback)

    def unsubscribe_all(self) -> None:
        self._provider.unsubscribe_all()

    # ---------------------------------------------------------- Cache management

    def clear_symbol(self, symbol: str, timeframe: Timeframe | None = None) -> int:
        """Delete all cached files for *symbol* (optionally filtered by timeframe).

        Returns:
            Number of files deleted.
        """
        pattern = f"{symbol.replace('/', '-')}_"
        if timeframe:
            pattern += f"{timeframe.value}_"
        deleted = 0
        for path in self._cache_dir.glob(f"{pattern}*"):
            path.unlink(missing_ok=True)
            deleted += 1
        with self._lock:
            for key in [k for k in self._memory if k.startswith(pattern)]:
                del self._memory[key]
        logger.info("Cleared %d cache files for %s", deleted, symbol)
        return deleted

    def clear_all(self) -> int:
        """Delete all cache files and the in-memory dict.

        Returns:
            Number of files deleted.
        """
        deleted = 0
        for path in self._cache_dir.glob("*.parquet"):
            path.unlink(missing_ok=True)
            deleted += 1
        for path in self._cache_dir.glob("*.meta.json"):
            path.unlink(missing_ok=True)
        for path in self._cache_dir.glob("*.json"):
            path.unlink(missing_ok=True)
        with self._lock:
            self._memory.clear()
        logger.info("Cleared all cache (%d files)", deleted)
        return deleted

    @property
    def cache_dir(self) -> Path:
        return self._cache_dir
