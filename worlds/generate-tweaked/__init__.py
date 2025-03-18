from worlds.LauncherComponents import components, Component, Type
import logging
def launch_client(*args) -> None:
    from .Generate_Tweaked import start
    try:
        start(*args)
    except Exception as e:
        logging.exception(e)
        if "--skip_prompt" not in args:
            input("Press enter to close.")

components.append(Component(
        "GenerateTweaked",
        cli=True,
        func=launch_client,
        component_type=Type.HIDDEN
    )
)

