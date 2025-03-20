# Archipelago-Tools

A Collection of tools I made to be used with [Archipelago](https://github.com/ArchipelagoMW/Archipelago)

Scripts in the root folder need to be dropped in the Archipelago folder to work.  
Any script in subfolders do not follow this rule.

## Root Scripts

### Generate_Tweaked.py

- Found [here](/worlds/generate-tweaked/)
- Inspired by [Archipelago fuzzer](https://github.com/Eijebong/Archipelago-fuzzer) from which I learned out how to call AP's generate.py
- A drop in "replacement" for Generate.py
- Can work either as an Apworld or from the script directly
  - To call the apworld do `Launcher.py/ArchipelagoLauncherDebug.exe GenerateTweaked -- [add arguments here the empty -- is important]`
  - For the script to work it must be copied to the AP source install folder directly  
    Then you can call it directly like so: `Generate_Tweaked.py [Arguments here]`
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
    - **Known exception for the Script version:** Doesn't stop the prompt when a yaml is invalid.
  - `--cache_modified_player_yamls`
    - Keep a cache of the modified player yamls named using the checksum of the player yamls. Useful for multi-process generation.
  - `--keep_folder_on_output`
    - When included the temporary/cache folder is not be deleted on successful output.

### async-roller-automate.bat

- Found [here](async-roller-automate.bat)
- Based on an earlier version of this script someone dropped in an async discussion on discord
- Batch script that let you automatically roll multiple generation at the same time
- it has a couple options in the 20 first lines of the script that let you customize the args it uses, where it take the player yamls and where it put the final zips
- Once launched it will ask a couple questions to tweak the generation
  - Simply press enter to use the default value
