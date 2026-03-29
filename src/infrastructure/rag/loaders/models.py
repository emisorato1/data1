from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class LoadedDocument:
    """Representa un documento cargado y procesado."""

    text: str
    metadata: dict[str, Any]
    pages: int
    tables_count: int = 0
    extra_info: dict[str, Any] = field(default_factory=dict)
