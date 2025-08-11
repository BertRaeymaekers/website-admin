import json
import os
from pathlib import Path


CONF_DIR = "conf"


current_working_directory = Path(os.getcwd())


def read_configuration(args):
    conf_file = current_working_directory / CONF_DIR / "default.json"
    if "conf" in args:
        conf_file = current_working_directory / CONF_DIR / f"{args["conf"][-1]}.json"
    print(f"Reading in configuration file {conf_file}")
    with open(conf_file, "r") as configuration:
        conf = json.load(configuration)
    if args["conf"][1:]:
        conf.update(read_configuration({"conf": args["conf"[1:]]}))
    for arg,value in args.items():
        if arg == "conf":
            conf[arg] = value[-1]
        else:
            conf[arg] = value
    if not "localdir" in conf:
        if "conf" in args:
            conf["localdir"] = current_working_directory / args["conf"][-1]
    return conf
