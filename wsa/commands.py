import os
from pathlib import Path

from git import Repo
from jinja2 import Environment, FileSystemLoader

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
    build_dir = current_working_directory / "build" / conf["localdir"]
    path = Path("build") / conf["conf"] 
    os.makedirs(path, exist_ok=True)
    env = Environment(loader = FileSystemLoader(f'templates/{conf["template"]}'))
    parameters = {}
    with open(path / "index.html", "w") as fh:
        fh.write(env.get_template("index.html.j2").render(conf | parameters))

