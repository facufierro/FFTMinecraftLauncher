from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Profile:
    created: Optional[str] = None
    icon: Optional[str] = "Furnance"
    lastUsed: Optional[str] = None
    lastVersionId: Optional[str] = None
    name: Optional[str] = None
    type: Optional[str] = None
    gameDir: Optional[str] = None
    javaArgs: Optional[str] = None
