from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Instance:
    name: str
    minecraft_version: str
    loader_version: str
    java_dir: Optional[str] = None
    mods_dir: Optional[str] = None
    mod_list: List[str] = field(default_factory=list)
    config_defaults_dir: Optional[str] = None
    kubejs_dir: Optional[str] = None
    local_dir: Optional[str] = None
    modflared_dir: Optional[str] = None
    resourcepacks_dir: Optional[str] = None
    resourcepacks: List[str] = field(default_factory=list)
