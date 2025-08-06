import os

from git import Repo
from  websiteadmin.configuration import current_working_directory, CONF_DIR, read_configuration


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
            elif key not in ["", "conf"]:
                print(f"    {key}: {conf[key]} ")


def pull(args):
    conf = read_configuration(args)
    local_dir = current_working_directory / conf["localdir"]
    repo_url = conf["gitrepo"]
    os.makedirs(local_dir, exist_ok=True)
    print("Local directory:", local_dir)
    print("Git repo URL:", repo_url)
    if os.path.exists(local_dir / ".git"):
        repo = Repo(local_dir)
        print("Pulling repo...")
        repo.remotes.origin.pull()
        print("Repo pulled.")
    else:
        print("Cloning repo...")
        repo = Repo.clone_from(repo_url, local_dir)
        print("Repo cloned.")
