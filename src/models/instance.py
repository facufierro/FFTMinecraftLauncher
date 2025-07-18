from dataclasses import dataclass, field
from typing import Optional, List, Dict
from ..models.constants import Paths


@dataclass
class Instance:
    name: str
    current_versions: Dict[str, str] = field(default_factory=dict)
    required_versions: Dict[str, str] = field(default_factory=dict)
    instance_path: str = Paths.INSTANCE_DIR.value
    versions_file: str = Paths.VERSIONS_FILE.value
    mod_list: List[str] = field(default_factory=list)
    resourcepacks: List[Dict[str, str]] = field(default_factory=list)
    shaders: List[Dict[str, str]] = field(default_factory=list)
