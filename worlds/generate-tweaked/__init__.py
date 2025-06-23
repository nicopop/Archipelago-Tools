from worlds.LauncherComponents import components, Component, Type, launch
from typing import Optional, Callable
from .Generate_Tweaked import version, display_name
class VersionedComponent(Component):
    def __init__(self, display_name: str,  version: int = 0, icon: str = 'icon', cli: bool = False, func: Optional[Callable] = None, file_identifier: Optional[Callable[[str], bool]] = None, component_type: Optional[Type] = None):
        super().__init__(display_name=display_name, icon=icon, cli=cli, func=func, file_identifier=file_identifier, component_type=component_type)
        self.version = version


def launch_client(*args):
    from .Generate_Tweaked import start
    launch(start, name=display_name, args=args)

# Totally not taken straight from Manual no siree
# Is this Overkill? Definitely.
found = False
for c in components:
    if c.display_name == display_name:
        found = True
        if getattr(c, "version", 0) < version:  # We have a newer version of the GenerateTweaked than the one the last apworld added
            c.version = version
            c.func = launch_client

if not found:
    components.append(VersionedComponent(
        display_name,
        cli=True,
        version=version,
        func=launch_client,
        component_type=Type.TOOL
    )
)

