from dataclasses import dataclass, field
from typing import Optional, List, Dict


@dataclass
class Instance:
    name: str
    minecraft_version: str
    loader_version: str
    java_dir: Optional[str] = None
    mods_dir: Optional[str] = None
    mod_list: List[str] = field(default_factory=list)
    default_configs_dir: Optional[str] = None
    kubejs_dir: Optional[str] = None
    local_dir: Optional[str] = None
    modflared_dir: Optional[str] = None
    resourcepacks_dir: Optional[str] = None
    resourcepacks: List[Dict[str, str]] = field(default_factory=list)
    shaderpacks_dir: Optional[str] = None
    shaders: List[Dict[str, str]] = field(default_factory=list)
