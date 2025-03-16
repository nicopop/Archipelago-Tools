from worlds.LauncherComponents import components, Component, Type

def launch_client(*args) -> None:
    from .Generate_Tweaked import start
    import multiprocessing
    # Inspired from AP's launch_subprocess but tweaked to get the prompt to work like generate
    # Doing this with a process because otherwise it doesn't gen. For some reason that idk enough about internal AP to fix
    process = multiprocessing.Process(target=start, name="GenerateTweaked", args=args)
    process.start()
    process.join()
    if "--skip_prompt" not in args and process.exitcode is not None and process.exitcode > 0:
        input("Press enter to close.")

components.append(Component(
        "GenerateTweaked",
        cli=True,
        func=launch_client,
        component_type=Type.HIDDEN
    )
)

