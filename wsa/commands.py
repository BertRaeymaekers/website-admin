import contextlib
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer, test
import os
from pathlib import Path
import re
import shutil
import socket

from git import Repo
from jinja2 import Environment, FileSystemLoader
import markdown
import yaml

from  wsa.configuration import current_working_directory, CONF_DIR, read_configuration
from wsa.lib.jinja2_helpers import register_in_template


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
    build = True
    if "pull" in args:
        build = False
        conf, fetch_info = pull(args)
        if fetch_info[0].old_commit:
            print("Nothing changed.")
            build = True
        elif "force" in args:
            build = True
    else:
        conf = read_configuration(args)
    
    if not build:
        print("Nothing changed upon pull, so not building. Override with the --force flag.")
        return (conf, None)

    src_dir = current_working_directory / "src" / conf["localdir"]
    build_dir = current_working_directory / "build" / conf["conf"]
    os.makedirs(build_dir, exist_ok=True)
    env = Environment(loader = FileSystemLoader(f'templates/{conf["template"]}'))

    os.makedirs(build_dir / "downloads", exist_ok=True)
    for file in os.listdir(src_dir / "downloads"):
        filename = os.fsdecode(file)
        base = filename.rsplit(".", 1)[0]
        shutil.copy(src_dir / "downloads" / filename, build_dir / "downloads" / filename)

    parameters = {}
    for file in os.listdir(src_dir):
        filename = os.fsdecode(file)
        if filename.endswith(".yaml"):
            fn_parts = filename.split(".")[:-1]
            with open(src_dir / filename) as yaml_stream:
                extra_params = yaml.safe_load(yaml_stream)
                downloads = {}
                if fn_parts[0] in extra_params and "downloads" in extra_params[fn_parts[0]]:
                    pattern = re.compile(extra_params[fn_parts[0]]["downloads"]["regex"])
                    for download_file in sorted(os.listdir(build_dir / "downloads"), reverse=True):
                        if pattern.match(download_file):
                            downloads[download_file] = f"/downloads/{download_file}"
                temp = parameters
                for part in fn_parts:
                    temp[part] = {}
                    if downloads:
                        if "data" not in extra_params[part]:
                            extra_params[part]["data"] = {}
                        extra_params[part]["data"]["downloads"] = downloads
                print("###", filename, "###")
                print(temp, part, extra_params, fn_parts[0])
                print("###", "---", "###")
                try:
                    temp[part] = extra_params[fn_parts[0]]
                    print(temp[part])
                except KeyError as ke:
                    print("KeyError", ke)
            continue
        elif filename.endswith(".gif") or filename.endswith(".png") or filename.endswith(".jpeg") or filename.endswith(".jpg") or filename.endswith(".ico"):
            shutil.copy(src_dir / filename, build_dir / filename)
        else:
            continue

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

    os.makedirs(build_dir / "img", exist_ok=True)
    for file in os.listdir(src_dir / "img"):
        filename = os.fsdecode(file)
        base = filename.rsplit(".", 1)[0]
        if filename.endswith(".gif") or filename.endswith(".png") or filename.endswith(".jpeg") or filename.endswith(".jpg"):
            shutil.copy(src_dir / "img" / filename, build_dir / "img" / filename)

    past_dir = parameters.get("past", {}).get("folder", "past")
    future_dir = parameters.get("future", {}).get("folder", "future")
    os.makedirs(build_dir / past_dir, exist_ok=True)
    os.makedirs(build_dir / future_dir, exist_ok=True)
    parameters["past"]["pages"] = []
    parameters["future"]["pages"] = []
    for file in os.listdir(src_dir / "events"):
        filename = os.fsdecode(file)
        if filename.endswith(".yaml"):
            fn_parts = filename.split(".")[:-1]
            with open(src_dir / "events" / filename) as yaml_stream:
                event_params = yaml.safe_load(yaml_stream)
                html_filename = f"{filename.rsplit(".", 1)[0]}.html"
                if "body" in event_params or "slides" in event_params:
                    parameters["past"]["pages"].append(event_params | {"link": f"{past_dir}/{html_filename}"})
                    for md in ["body", "announcement"]:
                        if md in event_params:
                            event_params[md] = markdown.markdown(event_params[md]).replace("<img ", '<img class="fullwidth" ')
                    print(f"Generating {past_dir}/{html_filename} from past.html.j2")
                    with open(build_dir / past_dir / html_filename, "w") as fh:
                        template = env.get_template("past.html.j2")
                        register_in_template(template)
                        fh.write(template.render(conf | parameters | event_params))
                if "announcement" in event_params:
                    future_item_params = {"link": f"{future_dir}/{html_filename}"}
                    if "download" in event_params:
                        future_item_params["download"] = event_params["download"]
                    parameters["future"]["pages"].append(event_params | future_item_params)
                    for md in ["announcement"]:
                        if md in event_params:
                            event_params[md] = markdown.markdown(event_params[md]).replace("<img ", '<img class="fullwidth" ')
                    for missing in ["slides"]:
                        # Overwriting some parameters from the main configuration with empties.
                        if missing not in event_params:
                            event_params[missing] = {}
                    print(f"Generating {future_dir}/{html_filename} from future.html.j2")
                    with open(build_dir / future_dir / html_filename, "w") as fh:
                        template = env.get_template("future.html.j2")
                        register_in_template(template)
                        fh.write(template.render(conf | parameters | event_params))


    print("Generating index.html from index.html.j2")
    with open(build_dir / "style.css", "w") as fh:
        fh.write(env.get_template("style.css.j2").render(conf | parameters))
    
    with open(build_dir / "index.html", "w") as fh:
        template = env.get_template("index.html.j2")
        register_in_template(template)
        fh.write(template.render(conf | parameters))

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
                        template = env.get_template(f"{template}.html.j2")
                        register_in_template(template)
                        fh.write(template.render(conf | parameters | data))
        return (conf, build_dir)

def serve(args):
    if "build" in args:
        build = False
        conf, build_dir = build(args)
    else:
        conf = read_configuration(args)
        build_dir = current_working_directory / "build" / conf["conf"]

    class DualStackServer(ThreadingHTTPServer):
        def server_bind(self):
            # suppress exception when protocol is IPv4
            with contextlib.suppress(Exception):
                self.socket.setsockopt(
                    socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
            return super().server_bind()

        def finish_request(self, request, client_address):
            self.RequestHandlerClass(request, client_address, self,
                                     directory=build_dir)

    if "port" in args:
        port=args["port"][-1]
    else:
        port = 8080
    if "bind" in args:
        bind=args["bind"][-1]
    else:
        bind = "127.0.0.1"
    if "protocol" in args:
        protocol=args["protocol"][-1]
    else:
        protocol="HTTP/1.0"
    print(f"Connect to http://{bind}:{port}/")
    test(
        HandlerClass=SimpleHTTPRequestHandler,
        ServerClass=DualStackServer,
        port=port,
        bind=bind,
        protocol=protocol
    )

def publish(args):
    if "build" in args:
        conf, build_dir = build(args)
    else:
        conf = read_configuration(args)
        build_dir = current_working_directory / "build" / conf["conf"]
