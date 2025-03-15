# Archipelago-Tools

A Collection of tools I made to be used with [Archipelago](https://github.com/ArchipelagoMW/Archipelago)

Scripts in the root folder need to be dropped in the Archipelago folder to work.  
Any script in subfolders do not follow this rule.

## Root Scripts

### Generate-Tweaked.py

- Found [here](Generate-Tweaked.py)
- Inspired by [Archipelago fuzzer](https://github.com/Eijebong/Archipelago-fuzzer) from which I learned out how to call AP's generate.py
- A drop in "replacement" for Generate.py
- Every argument Generate.py support works with it
- Some custom Arguments are added:
  - `--max_prog_balancing -1/[0-99]` default: -1
    - Any value other than -1 will decide the maximum prog_balancing allowed in the generation
    - Any value above that setting will get clamped down to it
    - Even Random, Random-range and custom ranges are clamped
  - An alternative to the Argument is to add a `max_progression_balancing` setting to your meta.yaml to use this in a more complex way
    - Any Value the main prog_balancing option supports is compatible
    - The maximum can be set per game
    - Check the [template](meta.yaml) for an example
  - `--skip_prompt`
    - When added disable the "Press enter to close"
    - Useful when combined with some script like [automatic async roller](async-roller-automate.bat) to let the generator start over automatically on failure.
    - **Known exception:** Doesn't stop the prompt when a yaml is invalid.

### async-roller-automate.bat

- Found [here](async-roller-automate.bat)
- Based on an earlier version of this script someone dropped in an async discussion on discord
- Batch script that let you automatically roll multiple generation at the same time
- it has a couple options in the 22 first lines of the script that let you customize what program is used to generate, where to take the player yamls and where to put the final zips
- Once launched it will ask a couple questions to tweak the generation
  - Simply press enter to use the default value
  - folderVariant mean the name of a subfolder in the player/output folder to use
    - EX: `8th` will check files in `Players\8th\`
