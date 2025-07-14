from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Profile:
    id: Optional[str] = None
    created: Optional[str] = None
    icon: Optional[str] = "Furnance"
    lastUsed: Optional[str] = None
    lastVersionId: Optional[str] = None
    name: Optional[str] = None
    type: Optional[str] = None
    gameDir: Optional[str] = None
    javaArgs: Optional[str] = None

    def __repr__(self):
        return (
            f"id: {self.id}, \n"
            f"created: {self.created}, \n"
            f"icon: {self.icon}, \n"
            f"lastUsed: {self.lastUsed}, \n"
            f"lastVersionId: {self.lastVersionId}, \n"
            f"type: {self.type}, \n"
            f"gameDir: {self.gameDir}, \n"
            f"javaArgs: {self.javaArgs}"
        )
