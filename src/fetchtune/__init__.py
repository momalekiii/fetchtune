from __future__ import annotations

from fetchtune.models import Album, Artist, Track
from fetchtune.resolver import (
    Resolver,
    ResolverError,
    get_default_resolver,
    resolve,
    try_resolve,
)

__all__ = [
    "Album",
    "Artist",
    "Track",
    "Resolver",
    "ResolverError",
    "get_default_resolver",
    "resolve",
    "try_resolve",
]

__version__ = "0.1.0"
