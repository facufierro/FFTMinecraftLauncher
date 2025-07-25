import os
from dataclasses import dataclass, field
from typing import Optional, List, Dict


@dataclass
class Instance:
    instance_dir: str
    defaultconfigs_dir: str = field(init=False)
    config_dir: str = field(init=False)
    kubejs_dir: str = field(init=False)
    modflared_dir: str = field(init=False)
    mods_dir: str = field(init=False)
    resourcepacks_dir: str = field(init=False)
    shaders_dir: str = field(init=False)
    servers_file: Optional[str] = field(init=False)
    mod_list: List[str] = field(default_factory=list)
    resourcepacks: List[Dict[str, str]] = field(default_factory=list)
    shaders: List[Dict[str, str]] = field(default_factory=list)

    def __post_init__(self):
        self.defaultconfigs_dir = os.path.join(self.instance_dir, "defaultconfigs")
        self.config_dir = os.path.join(self.instance_dir, "config")
        self.kubejs_dir = os.path.join(self.instance_dir, "kubejs")
        self.modflared_dir = os.path.join(self.instance_dir, "modflared")
        self.mods_dir = os.path.join(self.instance_dir, "mods")
        self.resourcepacks_dir = os.path.join(self.instance_dir, "resourcepacks")
        self.shaders_dir = os.path.join(self.instance_dir, "shaderpacks")
        self.servers_file = os.path.join(self.instance_dir, "servers.dat")
