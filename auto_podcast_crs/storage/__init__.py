"""StorageProvider interface — upload local files to a public URL."""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class StorageProvider(ABC):
    """Uploads a local file and returns a public URL."""

    @abstractmethod
    def upload(
        self,
        local_path: Path,
        object_key: str,
        *,
        content_type: str | None = None,
    ) -> str:
        """Upload local_path to object_key. Return public URL."""
        ...

    @abstractmethod
    def exists(self, object_key: str) -> bool:
        """True if object_key is already present in storage."""
        ...
