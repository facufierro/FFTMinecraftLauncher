from dataclasses import dataclass, field
from typing import Optional, List, Dict
from ..models.constants import get_minecraft_dir, get_instance_dir, get_versions_file


@dataclass
class Instance:
    name: str
    game_dir: str = field(default_factory=get_minecraft_dir)
    current_versions: Dict[str, str] = field(default_factory=dict)
    required_versions: Dict[str, str] = field(default_factory=dict)
    instance_path: str = field(default_factory=get_instance_dir)
    versions_file: str = field(default_factory=get_versions_file)
    mod_list: List[str] = field(default_factory=list)
    resourcepacks: List[Dict[str, str]] = field(default_factory=list)
    shaders: List[Dict[str, str]] = field(default_factory=list)
