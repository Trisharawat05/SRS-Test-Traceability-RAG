from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class DocumentContent:

    file_name: str

    file_type: str

    text: str = ""

    pages: List[Dict[str, Any]] = field(
        default_factory=list
    )

    tables: List[Dict[str, Any]] = field(
        default_factory=list
    )

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )