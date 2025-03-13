import sys, os
from pathlib import Path

args = sys.argv
droppedMode = False
if len(args) > 1:
    droppedMode = True

abspath = os.path.dirname(__file__)
input_folder = os.path.join(abspath, "input")
output_folder = os.path.join(abspath, "output")
output_filename = "" # Change this to define the final file name instead of the first yaml found

if not droppedMode:
    os.makedirs(input_folder, exist_ok=True)
os.makedirs(output_folder, exist_ok=True)

if droppedMode:
    Inputs = [f for f in args if f is not args[0]]
    Inputs.sort(key = lambda x: os.path.basename(x))
else:
    Inputs = [os.path.join(input_folder, f) for f in os.listdir(input_folder) if os.path.isfile(os.path.join(input_folder, f)) and os.path.splitext(f)[-1] in [".txt", ".yaml"]]
    Inputs.sort(key = lambda x: os.path.basename(x))

if Inputs:
    yamls: list[list[str]] = []
    i = 0
    for file in Inputs:
        name = os.path.basename(file)
        yamls.append([f"# original yaml: {name}"])
        with open(file, "r", encoding="utf-8" ) as f:
            for line in f:
                processed = line.rstrip().lstrip("﻿") #strip zero width spaces just in case
                yamls[i].append(f"{processed}")
        i += 1
    if output_filename:
        path = os.path.join(output_folder, output_filename + ".yaml")
    else:
        path = os.path.join(output_folder, Path(os.path.basename(Inputs[0])).stem + ".yaml")
    with open(path, "w+", encoding="utf-8") as f:
        for i in range(len(yamls)):
            if i > 0:
                f.write("\n---\n\n")
            for line in yamls[i]:
                f.write(f"{line}\n")
