from __future__ import annotations

from abc import ABC, abstractmethod

from fetchtune.models import Track


class Provider(ABC):
    """
    Base class for all music providers.
    """

    name: str = ""

    @abstractmethod
    def can_handle(self, url: str) -> bool:
        """
        Return True if this provider supports the given URL.
        """
        raise NotImplementedError

    @abstractmethod
    def resolve(self, url: str) -> Track:
        """
        Resolve a supported URL into a Track object.
        """
        raise NotImplementedError