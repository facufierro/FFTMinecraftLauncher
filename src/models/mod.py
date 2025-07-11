from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Mod:
    name: str
    version: str
    authors: List[str] = field(default_factory=list)
    description: Optional[str] = None
    website: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
