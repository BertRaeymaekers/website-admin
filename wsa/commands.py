import os
from pathlib import Path
import shutil

from git import Repo
from jinja2 import Environment, FileSystemLoader
import yaml

from  wsa.configuration import current_working_directory, CONF_DIR, read_configuration


def conf(args):
    if "list" in args:
        print("Configurations:")
        for file in os.listdir(current_working_directory / CONF_DIR):
            filename = os.fsdecode(file)
            if filename.endswith(".json"):
                print(f"    {filename.rsplit(".", 1)[0]}")
        print()
    if "conf" in args:
        conf = read_configuration(args)
        print()
        print("Configuration:")
        for key in sorted(conf):
            if key.lower().endswith("password"):
                print(f"    {key}: ******")
            elif key not in [""]:
                print(f"    {key}: {conf[key]} ")


def pull(args):
    conf = read_configuration(args)
    src_dir = current_working_directory / "src" / conf["localdir"]
    repo_url = conf["gitrepo"]
    os.makedirs(src_dir, exist_ok=True)
    print("Local directory:", src_dir)
    print("Git repo URL:", repo_url)
    if os.path.exists(src_dir / ".git"):
        repo = Repo(src_dir)
        print("Pulling repo...")
        fetch_infos = repo.remotes.origin.pull()
        print(fetch_infos[0])
        print("Repo pulled.")
        return (conf, fetch_infos)
    else:
        print("Cloning repo...")
        repo = Repo.clone_from(repo_url, src_dir)
        print("Repo cloned.")
        return (conf, repo)


def build(args):
    if "pull" in args:
        conf, fetch_info = pull(args)
    else:
        conf = read_configuration(args)
    src_dir = current_working_directory / "src" / conf["localdir"]
    build_dir = current_working_directory / "build" / conf["conf"]
    os.makedirs(build_dir, exist_ok=True)
    env = Environment(loader = FileSystemLoader(f'templates/{conf["template"]}'))
    parameters = {}
    for file in os.listdir(src_dir):
        filename = os.fsdecode(file)
        if filename.endswith(".yaml"):
            fn_parts = filename.split(".")[:-1]
            with open(src_dir / filename) as yaml_stream:
                extra_params = yaml.safe_load(yaml_stream)
                temp = parameters
                for part in fn_parts:
                    temp[part] = {}
                print(temp, part, extra_params, fn_parts[0])
                try:
                    temp[part] = extra_params[fn_parts[0]]
                except KeyError as ke:
                    print("KeyError", ke)
            continue
        elif filename.endswith(".gif") or filename.endswith(".png") or filename.endswith(".jpeg") or filename.endswith(".jpg"):
            shutil.copy(src_dir / filename, build_dir / filename)
        else:
            continue

    if "slides" in parameters:
        if not parameters["slides"]:
            parameters["slides"] =  {}
        os.makedirs(build_dir / "slides", exist_ok=True)
        for file in os.listdir(src_dir / "slides"):
            filename = os.fsdecode(file)
            base = filename.rsplit(".", 1)[0]
            if filename.endswith(".gif") or filename.endswith(".png") or filename.endswith(".jpeg") or filename.endswith(".jpg"):
                shutil.copy(src_dir / "slides" / filename, build_dir / "slides" / filename)
                if base not in parameters["slides"]:
                    parameters["slides"][base] = {}
                parameters["slides"][base]["img"] = f"slides/{filename}"
                if "txt" not in parameters["slides"][base]:
                    parameters["slides"][base]["txt"] = base.replace("_", " ")

    print("Parameters:", parameters)
    print("Generating index.html from index.html.j2")
    with open(build_dir / "index.html", "w") as fh:
        fh.write(env.get_template("index.html.j2").render(conf | parameters))

    if "menu" in parameters:
        for menuitem in parameters["menu"]:
            if "link" in menuitem:
                link = menuitem["link"]
                if link.startswith("/") and link.endswith(".html"):
                    # Local link, and not the index
                    name = link[1:].rsplit(".", 1)[0]
                    template = "index"
                    data = parameters.get(name, {}).get("data",  {})
                    if "title" not in data:
                        data["title"] = menuitem["title"]
                    if name in parameters:
                        if "template" in parameters[name]:
                            template = parameters[name]["template"]
                    print(f"Generating {name}.html from {template}.html.j2 with data:", data)
                    with open(build_dir / f"{name}.html", "w") as fh:
                        fh.write(env.get_template(f"{template}.html.j2").render(conf | parameters | data))
        return (conf, build_dir)


def publish(args):
    if "build" in args:
        conf, build_dir = build(args)
    else:
        conf = read_configuration(args)
        build_dir = current_working_directory / "build" / conf["conf"]


