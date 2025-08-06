from collections import defaultdict
import sys

from websiteadmin.commands import conf, pull



USAGE_DEFAULT = """USAGE:
    websiteadmin --help
"""

USAGE = {
    "pull": """        websiteadmin pull --conf <conf>
            --conf <conf>: Name of the configuration.
    """,
    "conf": """        websiteadmin conf [--list] [--conf <conf>]
            --list: List all the configurations.
            --conf <conf>: Name of the configuration.
    """
}


COMMANDS = {
    "conf": (conf, "Check the configuration"),
    "pull": (pull, "Pull the latest version from the git repo")
}


def help(message:str=None, args:dict=None, rc:int=None):
    command = " ".join(args.get("", args.get("help", [])))
    if message:
        print(message)
        print()
    elif command not in USAGE:
        print(f"Unknown command '{command}'")
    if args is None:
        args =  {"help": True}
    print(USAGE_DEFAULT)
    if command in COMMANDS:
        print(f"    {COMMANDS[command][1]}:")
    if command in USAGE:
        print(USAGE.get(command, ""))
    if rc is not None:
        sys.exit(rc)


args = defaultdict(list)
parameter = ""
ignore_parameter = False
for arg in sys.argv[1:]:
    if arg.startswith("--") and not ignore_parameter:
        if arg == "--":
            ignore_parameter = True
            continue
        if parameter:
            help(message=f"You need to specify a value for --{parameter}.", rc=1)
        parameter = arg[2:].lower()
    else:
        if parameter:
            args[parameter].append(arg)
            parameter = ""
        else:
            args[""].append(arg)
if parameter:
    args[parameter].append(arg)

if "help" in args:
    help(args=args, rc=0)

command = ".".join(args[""])
if not command:
    help("Please enter command", args=args, rc=1)
try:
    method = COMMANDS[command][0]
except KeyError:
    help("Wrong command", args=args, rc=1)

print("Arguments:", args)
method(args)
