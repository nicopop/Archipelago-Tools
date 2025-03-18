import os, logging, yaml, random, tempfile, shutil, zlib
from datetime import datetime
from pathlib import Path
from Generate import main as GenMain, read_weights_yamls
from Main import main as ERmain
from argparse import ArgumentParser, ArgumentTypeError, Namespace
from BaseClasses import PlandoOptions, get_seed
from Options import ProgressionBalancing
from typing import Tuple, Any, Dict
from Utils import version_tuple, init_logging


def main(args: Namespace):
#region meta.yaml
    if args.weights_file_path and os.path.exists(args.weights_file_path):
        try:
            weights_file = read_weights_yamls(args.weights_file_path)[-1]
        except Exception as e:
            raise ValueError(f"File {args.weights_file_path} is invalid. Please fix your yaml.") from e
        logging.info(f"Weights: {args.weights_file_path} >> "
                     f"{get_choice('description', weights_file, 'No description specified')}")
    else:
        weights_file = {}
    if args.meta_file_path and os.path.exists(args.meta_file_path):
        try:
            meta_weights = read_weights_yamls(args.meta_file_path)[-1]
        except Exception as e:
            raise ValueError(f"File {args.meta_file_path} is invalid. Please fix your yaml.") from e
        logging.info(f"Meta: {args.meta_file_path} >> {get_choice('meta_description', meta_weights)}")
        try:  # meta description allows us to verify that the file named meta.yaml is intentionally a meta file
            tmp = meta_weights["meta_description"]
            del(meta_weights["meta_description"])
            meta_weights["meta_description"] = tmp
        except Exception as e:
            raise ValueError("No meta description found for meta.yaml. Unable to verify.") from e
        if args.sameoptions:
            raise Exception("Cannot mix --sameoptions with --meta")
    else:
        meta_weights = {}

    if args.max_prog_balancing == -1:
        root = meta_weights.get(None, {})
        args.max_prog_balancing = handle_meta_prog_bal_value(get_choice("max_progression_balancing", root, 99))

# endregion weights.yaml + meta.yaml processing

    player_path = args.player_files_path
    player_cache = loadplayers(player_path)

# region prog_balancing
    def prog_balancing_adjustments():
        logging.info("Analazing the yamls for prog_balancing values above the maximum allowed")
        for player, player_yaml in player_cache.items():
            i = 0
            for sub_yaml in player_yaml:
                games = get_choice("game", sub_yaml, "Archipelago", True)
                name = get_choice("name", sub_yaml, "")
                if isinstance(games, str):
                    games = [games]
                elif isinstance(games, dict):
                    games = list(games.keys())
                for option_key, option in sub_yaml.items():
                    if option_key not in games:
                        continue
                    max_prog = handle_meta_prog_bal_value(get_choice("max_progression_balancing", meta_weights.get(option_key, {}), args.max_prog_balancing))
                    prog_bal_value: dict[Any, int]|int|str|None = get_choice("progression_balancing", option, None, True)

                    if prog_bal_value is None:
                        prog_bal_value = handle_meta_prog_bal_value(ProgressionBalancing.default)

                    if isinstance(prog_bal_value, dict):
                        found_any = False
                        for pb_key, weight in dict(prog_bal_value.items()).items():
                            if weight == 0:
                                continue
                            proccessed = process_prog_bal_value(pb_key, max_prog)
                            if proccessed is not None:
                                found_any = True
                                del player_cache[player][i][option_key]["progression_balancing"][pb_key]
                                if proccessed not in player_cache[player][i][option_key]["progression_balancing"].keys():
                                    player_cache[player][i][option_key]["progression_balancing"][proccessed] = weight
                                else:
                                    player_cache[player][i][option_key]["progression_balancing"][proccessed] += weight #combine the weight
                        if found_any:
                            logging.debug(f"Found a value in {player}'s yaml in {name}->{option_key} above {max_prog}.")
                    else:
                        proccessed = process_prog_bal_value(prog_bal_value, max_prog)
                        if proccessed is not None:
                            logging.debug(f"Found a value in {player}'s yaml in {name}->{option_key} above {max_prog}.")
                            player_cache[player][i][option_key]["progression_balancing"] = proccessed
                i += 1
# endregion prog_balancing

# region Dumping yaml
    def dump_yamls_to_folder(yaml_path_dir: str):
        logging.info(f"Creating new Yaml files in folder")
        if meta_weights and Path(player_path) in Path(args.meta_file_path).parents: # if its in the player folder
            player_cache[Path(args.meta_file_path).name] = [meta_weights]
        if weights_file and Path(player_path) in Path(args.weights_file_path).parents: # if its in the player folder
            player_cache[Path(args.weights_file_path).name] = [weights_file]

        for file, content in player_cache.items():
            yaml_path = os.path.join(yaml_path_dir, file)
            with open(yaml_path, "w+", encoding="utf-8") as f:
                yaml.dump_all(content, f, sort_keys=False)

# endregion Dumping yaml

# region Cache
    if args.cache_modified_player_yamls:
        checksum_cache = player_cache
        if meta_weights and Path(player_path) in Path(args.meta_file_path).parents: # if its in the player folder
            checksum_cache[Path(args.meta_file_path).name] = [meta_weights]
        if weights_file and Path(player_path) in Path(args.weights_file_path).parents: # if its in the player folder
            checksum_cache[Path(args.weights_file_path).name] = [weights_file]

        checksum: int=0
        for item in sorted(checksum_cache.items()):
            c1 = 1
            for t in item:
                c1 = zlib.adler32(bytes(repr(t),'utf-8'), c1)
            checksum=checksum ^ c1
        timestamped_checksum: str = f"{checksum}-{args.max_prog_balancing}-{datetime.today().strftime('%Y-%m-%d')}"

        folder = tempfile.gettempdir()
        yaml_path_dir = os.path.join(folder, "ApGenerateTweakedCache", timestamped_checksum)
        lockfilepath = os.path.join(yaml_path_dir, "lock.lck")
        if os.path.exists(yaml_path_dir): #probably wait if not done or use the data already there otherwise.
            logging.info(f"Found an existing Cache folder at '{yaml_path_dir}'.")
            if os.path.exists(lockfilepath):
                import time
                interval = 5
                waited = 0
                logging.info("Found a lock file, another process is still working on generation.")
                while os.path.exists(lockfilepath):
                    try:
                        tmp = open(lockfilepath, "r+")
                        logging.error("Seems like the lock file died ")
                        tmp.close()
                        raise Exception(f"The lock file got unlocked before being deleted. \nfound here: {lockfilepath}")
                    except IOError:
                        logging.debug("lock file is still locked, good.")
                    time.sleep(interval)
                    waited += interval
                    if waited > 3600: #1 hour
                        raise Exception("Waited too long for the lock file to get removed, you might have an issue or too many yamls")

        else: # this process is the first :D
            logging.info(f"No existing Cache folder found, Time to create it at '{yaml_path_dir}'.")
            os.makedirs(yaml_path_dir, exist_ok=True)
            FileName = open(lockfilepath,"w+")
            prog_balancing_adjustments()
            dump_yamls_to_folder(yaml_path_dir)
            FileName.close()
            os.remove(lockfilepath)
    else: # No cache
        yaml_path_dir = tempfile.mkdtemp(prefix="apgenerate")
        logging.info(f"Cache disabled, Time to do it all  at '{yaml_path_dir}'.")
        prog_balancing_adjustments()
        dump_yamls_to_folder(yaml_path_dir)

# endregion Cache

# region Generation
    args.player_files_path = yaml_path_dir # Update Args path for generation
    args.meta_file_path = os.path.join(yaml_path_dir, Path(args.meta_file_path).name)
    args.weights_file_path = os.path.join(yaml_path_dir, Path(args.weights_file_path).name)

    logging.info("Starting full Generation.")
    logging.info(f"Logs past this are saved in Generate_{args.seed}_{datetime.now().strftime('%Y_%m_%d_%H_%M_%S')}.txt")

    erargs, seed = GenMain(args)
    ERmain(erargs, seed)

    if not args.keep_folder_on_output:
        logging.info("Deleting Cache/temp folder")
        shutil.rmtree(yaml_path_dir) #if it didnt crash delete the folder
# endregion Generation

# region Misc functions
def handle_meta_prog_bal_value(value: str|int) -> int:
    if isinstance(value, int) and 0 <= value <= 99:
        return value
    option = ProgressionBalancing.from_any(value)
    return option.value

def get_choice(option, root, value=None, return_all = False) -> Any:
    if option not in root:
        return value
    if type(root[option]) is list:
        if return_all:
            return root[option]
        return random.choices(root[option])[0]
    if type(root[option]) is not dict:
        return root[option]
    if not root[option]:
        return value
    if any(root[option].values()):
        if return_all:
            return root[option]
        return random.choices(list(root[option].keys()), weights=list(map(int, root[option].values())))[0]
    raise RuntimeError(f"All options specified in \"{option}\" are weighted as zero.")

def get_range_values(range: str):
    range = range.removeprefix("random-range-")
    splits = range.split("-")
    if len(splits) == 2:
        return int(splits[0]), int(splits[1]), ""
    else:
        return int(splits[1]), int(splits[2]), splits[0]

def get_random_modifier(random: str) -> str:
    if not "-" in random:
        return ""
    splits = random.split("-")
    return splits[1]

def get_prog_bal_int_value(value: int|str|None) -> int|str:
    if value is None:
        return 99
    elif isinstance(value, int):
        return value

    try:
        intvalue = int(value)
    except ValueError as ex:
        if value in ProgressionBalancing.special_range_names.keys():
            intvalue = ProgressionBalancing.special_range_names[value]
        elif value.startswith("random"):
            if value.startswith("random-range"):
                intvalue = "range"
            else:
                intvalue = "random"
        else:
            raise ex
    return intvalue

def process_prog_bal_value(key: int|str, max_prog: int) -> None|str|int:
    processing = get_prog_bal_int_value(key)
    if isinstance(processing, str) and isinstance(key, str):
        replacement = None
        if processing == "random":
            modifier = get_random_modifier(key)
            replacement = f"random-range{'-' + modifier if modifier else ''}-0-{str(max_prog)}"
        elif processing == "range":
            modified = False
            rangevalues = get_range_values(key)
            min_value = rangevalues[0]
            max_value = rangevalues[1]
            modifier = rangevalues[2]
            if max_value > max_prog:
                modified = True
                max_value = max_prog
            if min_value > max_prog:
                modified = True
                min_value = max_prog
            if modified:
                replacement = f"random-range{'-' + modifier if modifier else ''}-{min_value}-{max_value}"
        return replacement
    elif isinstance(processing, int):
        if processing > max_prog:
            return max_prog

    return None
# endregion

# region yaml loading
def loadplayers(input_folder_name):
    weights_cache: Dict[str, Tuple[Any, ...]] = {}
    player_id = ""
    player_files: dict[str, list[dict[str, Dict[str, Any] | Any]]] = {}
    for file in os.scandir(input_folder_name):
        fname = file.name
        name = os.path.basename(file)
        if file.is_file() and not fname.startswith(".") and not fname.lower().endswith(".ini") and \
                name not in {"meta.yaml", "weight.yaml"}:
            path = os.path.join(input_folder_name, fname)
            try:
                weights_for_file = []
                for doc_idx, yaml in enumerate(read_weights_yamls(path)):
                    if yaml is None:
                        logging.warning(f"Ignoring empty yaml document #{doc_idx + 1} in {fname}")
                    else:
                        weights_for_file.append(yaml)
                weights_cache[fname] = tuple(weights_for_file)

            except Exception as e:
                raise ValueError(f"File {fname} is invalid. Please fix your yaml.") from e
    weights_cache = {key: value for key, value in sorted(weights_cache.items(), key=lambda k: k[0].casefold())}
    i = 0
    for filename, yaml_data in weights_cache.items():
        name = os.path.basename(filename)
        player_files[name] = []
        if name.lower() not in {"meta.yaml", "weight.yaml"}:
            for yaml in yaml_data:
                player_id = get_choice('name', yaml, 'No description specified')
                logging.info(f"P {i} ({player_id}) Weights: {filename} >> "
                             f"{get_choice('description', yaml, 'No description specified')}")
                player_files[name].append(yaml)
                i += 1
    return player_files
# endregion

# region Arguments
def mystery_argparse(Args: Tuple|list): # Modified arguments From 0.6.0 Generate.py
    from settings import get_settings
    def int_range(min_val: int, max_val: int):
        def int_range_checker(arg):
            """ Type function for argparse - a float within some predefined bounds """
            try:
                v = int(arg)
            except ValueError:
                raise ArgumentTypeError("Must be a floating point number")
            if v < min_val or v > max_val:
                raise ArgumentTypeError("Argument must be < " + str(max_val) + "and > " + str(max_val))
            return v
        return int_range_checker
    settings = get_settings()
    defaults = settings.generator

    parser = ArgumentParser(prog="APGenerateTweaked", description="CMD Generation Interface, defaults come from host.yaml.")
    parser.add_argument('--weights_file_path', default=defaults.weights_file_path,
                        help='Path to the weights file to use for rolling game options, urls are also valid')
    parser.add_argument('--sameoptions', help='Rolls options per weights file rather than per player',
                        action='store_true')
    parser.add_argument('--player_files_path', default=defaults.player_files_path,
                        help="Input directory for player files.")
    parser.add_argument('--seed', help='Define seed number to generate.', type=int)
    parser.add_argument('--multi', default=defaults.players, type=lambda value: max(int(value), 1))
    parser.add_argument('--spoiler', type=int, default=defaults.spoiler)
    parser.add_argument('--outputpath', default=settings.general_options.output_path,
                        help="Path to output folder. Absolute or relative to cwd.")  # absolute or relative to cwd
    parser.add_argument('--race', action='store_true', default=defaults.race)
    parser.add_argument('--meta_file_path', default=defaults.meta_file_path)

    default_loglevel = defaults.loglevel if hasattr(defaults, "loglevel") else settings.server_options.loglevel
    parser.add_argument('--log_level', default=default_loglevel, help='Sets log level')
    if version_tuple.minor >= 6:
        parser.add_argument('--log_time', help="Add timestamps to STDOUT",
                            default=defaults.logtime, action='store_true')

    parser.add_argument("--csv_output", action="store_true",
                        help="Output rolled player options to csv (made for async multiworld).")
    parser.add_argument("--plando", default=defaults.plando_options,
                        help="List of options that can be set manually. Can be combined, for example \"bosses, items\"")
    parser.add_argument("--skip_prog_balancing", action="store_true",
                        help="Skip progression balancing step during generation.")
    parser.add_argument('--max_prog_balancing', type=int_range(-1,99), default=-1,
                        help="Set the maximum level of progression balancing allowed, if set to any value other than -1") #Custom
    parser.add_argument("--skip_output", action="store_true",
                        help="Skips generation assertion and output stages and skips multidata and spoiler output. "
                             "Intended for debugging and testing purposes.")
    parser.add_argument("--skip_prompt", action="store_true",
                    help="Skips generation stopping with the 'press enter to close' prompt")
    parser.add_argument("--cache_modified_player_yamls", action="store_true",
                    help="Keep a cache of the modified player yamls. Useful for multi-process generation.")
    parser.add_argument("--keep_folder_on_output", action="store_true",
                    help="Should the temporary/cache folder not be deleted on succesful output")

    args: Namespace = parser.parse_args(Args)
    if not os.path.isabs(args.weights_file_path):
        args.weights_file_path = os.path.join(args.player_files_path, args.weights_file_path)
    if not os.path.isabs(args.meta_file_path):
        args.meta_file_path = os.path.join(args.player_files_path, args.meta_file_path)
    args.plando = PlandoOptions.from_option_string(args.plando)
    return args
# endregion

# region Start
def start(*args):
    args = mystery_argparse(args)
    args.seed = get_seed(args.seed)
    init_logging(f"GenerateTweaked_{args.seed}", loglevel=args.log_level)
    main(args)

if __name__ == '__main__':
    import sys
    import atexit
    args = mystery_argparse(sys.argv[1:])
    args.seed = get_seed(args.seed)
    init_logging(f"GenerateTweaked_{args.seed}", loglevel=args.log_level)
    confirmation = atexit.register(input, "Press enter to close.")
    if args.skip_prompt: atexit.unregister(confirmation)
    main(args)
    # in case of error-free exit should not need confirmation
    atexit.unregister(confirmation)
# endregion
