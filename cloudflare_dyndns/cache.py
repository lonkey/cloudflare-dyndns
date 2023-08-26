import ssl
from pathlib import Path
from typing import Dict, Optional, Union

import truststore
from pydantic import BaseModel

from . import printer
from .types import IPAddress

ssl_context = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)


class InvalidCache(Exception):
    """Raised when we can't read the cache.
    It's either corrupted, an older version or unreadable.
    """


class ZoneRecord(BaseModel):
    zone_id: str
    record_id: str
    proxied: bool = False


class IPCache(BaseModel):
    address: Optional[IPAddress] = None
    updated_domains: Dict[str, ZoneRecord] = dict()

    def clear(self):
        self.address = None
        self.updated_domains = dict()


class Cache(BaseModel):
    ipv4 = IPCache()
    ipv6 = IPCache()


class CacheManager:
    def __init__(
        self, cache_path: Union[str, Path], force: bool = False, *, debug: bool = False
    ):
        self._path = Path(cache_path).expanduser()
        self._force = force
        self._debug = debug

    def ensure_path(self):
        if self._debug:
            printer.info(f"Creating cache directory: {self._path}")
        self._path.parent.mkdir(exist_ok=True, parents=True)

    def load(self) -> Cache:
        if self._force:
            return Cache()

        try:
            return self._load()
        except InvalidCache:
            self.delete()

        return Cache()

    def _load(self):
        printer.info(f"Loading cache from: {self._path}")
        try:
            cache_json = self._path.read_text()
            cache = Cache.parse_raw(cache_json)
        except FileNotFoundError:
            printer.info(f"Cache file not found.")
            return Cache()
        except Exception:
            message = "Invalid cache file"
            if self._debug:
                message += ": {cache_json}"
            printer.warning(message)
            raise InvalidCache

        if self._debug:
            printer.info(f"Loaded cache: {cache}")
        return cache

    def save(self, cache: Cache):
        cache_json = cache.json()
        if self._debug:
            printer.info(f"Saving cache: {cache_json}")
        printer.info(f"Saving cache to: {self._path}")
        self._path.write_text(cache_json)

    def delete(self):
        printer.warning(f"Deleting cache at: {self._path}")
        self._path.unlink(missing_ok=True)
