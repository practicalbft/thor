"""Bootstraps a local setup of an app according to config in default.ini."""
from conf import config
from helpers import io
from shutil import which
import subprocess
import os
import json

HOST = "localhost"
IP_ADDR = "127.0.0.1"


def generate_heimdall_sd():
    """
    Generates the service discovery file used by the Prometheus container
    in Heimdall.
    """
    path = config.get_heimdall_sd_path()
    sd = {"targets": [], "labels": {"mode": "local", "job": "bft-list"}}

    # add all instances on Docker host to targets (only in local mode)
    for i in range(0, config.get_node_count()):
        sd["targets"].append("host.docker.internal:{}".format(6000 + int(i)))

    json_string = json.dumps([sd])
    io.write_file(path, json_string)
    return


def create_nodes_file():
    """Creates nodes.txt and writes it to specified directory."""
    n = config.get_node_count()
    app_path = config.get_app_path()
    hosts_path = config.get_hosts_path()

    contents = ""
    for i in range(0, n):
        contents = contents + \
            "{id},{host},{ip_addr},{port}\n".format(
                id=str(i), host=HOST, ip_addr=IP_ADDR, port=str(5000 + i))

    path = "{app_path}/{hosts_path}".format(
        app_path=app_path, hosts_path=hosts_path)
    io.write_file(path=path, contents=contents)


def start_heimdall():
    """
    Starts the Heimdall service.

    Given that docker-compose is available and path to Heimdall project root
    is specified, this methods starts heimdall as a subprocess.
    """
    dc = "docker-compose"
    if which(dc) is None:
        raise EnvironmentError("Can't find installation of docker-compose.")

    path = config.get_heimdall_root()
    print(path)
    if io.exists(path):
        with open("logs/heimdall.log", "w") as f:
            subprocess.Popen("{} down && {} up".format(dc, dc), shell=True,
                             cwd=path, stdout=f, stderr=f)
            print("Starting Heimdall..")
    else:
        raise ValueError("Heimdall root {} does not exists".format(path))


def bootstrap(start_metrics):
    """Launches a local environment according to specs in default.ini."""
    create_nodes_file()
    generate_heimdall_sd()
    if start_metrics:
        start_heimdall()

    cmd = config.get_entrypoint()
    cwd = config.get_app_path()
    env = os.environ.copy()

    for i in range(0, config.get_node_count()):
        env["ID"] = str(i)
        env["API_PORT"] = str(4000 + i)
        io.create_folder("logs")
        print("Starting app on node {}".format(i))
        with open("logs/node{i}.log".format(i=i), "w") as f:
            subprocess.Popen(cmd, shell=True, cwd=cwd, stdin=f, stderr=f,
                             env=env)
    return
