from pathlib import Path
from typing import Dict, Optional, Union
import click
from pydantic import BaseModel
from .types import Domain, IPv4or6Address


class InvalidCache(Exception):
    """Raised when we can't read the cache.
    It's either corrupted, an older version or unreadable.
    """


class ZoneRecord(BaseModel):
    zone_id: str
    record_id: str


class IPCache(BaseModel):
    address: Optional[IPv4or6Address] = None
    updated_domains: Dict[Domain, ZoneRecord] = dict()

    def clear(self):
        self.address = None
        self.updated_domains = dict()


class Cache(BaseModel):
    ipv4 = IPCache()
    ipv6 = IPCache()


class CacheManager:
    def __init__(self, cache_path: Union[str, Path], *, debug: bool = False):
        self._path = Path(cache_path).expanduser()
        self._debug = debug

    def ensure_path(self):
        if self._debug:
            click.echo(f"Creating cache directory: {self._path}")
        self._path.parent.mkdir(exist_ok=True, parents=True)

    def load(self) -> Cache:
        click.echo(f"Loading cache from: {self._path}")
        try:
            cache_json = self._path.read_text()
            cache = Cache.parse_raw(cache_json)
        except FileNotFoundError:
            click.echo(f"Cache file not found.")
            return Cache()
        except Exception:
            message = "Invalid cache file"
            if self._debug:
                message += ": {cache_json}"
            click.secho(message, fg="yellow")
            raise InvalidCache

        if self._debug:
            click.echo(f"Loaded cache: {cache}")
        return cache

    def save(self, cache: Cache):
        cache_json = cache.json()
        if self._debug:
            click.echo(f"Saving cache: {cache_json}")
        click.echo(f"Saving cache to: {self._path}")
        self._path.write_text(cache_json)

    def delete(self):
        click.secho(f"Deleting cache at: {self._path}", fg="yellow")
        self._path.unlink(missing_ok=True)
