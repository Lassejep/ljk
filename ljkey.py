#!/usr/bin/env python3
import ssl
import websockets
import asyncio
import curses
import argparse
import pathlib
import configparser
from src.view import console


def create_config():
    current_dir = pathlib.Path(__file__).parent
    config = configparser.ConfigParser()
    config["Client"] = {
        "host": "0.0.0.0",
        "port": "5039",
    }

    with open(f"{current_dir}/client.conf", "w") as configfile:
        config.write(configfile)


def read_config(current_dir):
    config = configparser.ConfigParser()
    config.read(f"{current_dir}/client.conf")
    return config


def arg_parser():
    parser = argparse.ArgumentParser(description="Password Manager Client")
    parser.add_argument(
        "-H", "--host",
        help="Host to connect to"
    )
    parser.add_argument(
        "-p", "--port",
        help="Port to connect to"
    )
    parser.add_argument(
        "--set-host",
        help="Set the host in the config file"
    )
    parser.add_argument(
        "--set-port",
        help="Set the port in the config file"
    )

    args = parser.parse_args()
    return args


def load_args(config, current_dir):
    args = arg_parser()
    if args.set_host:
        config["Client"]["host"] = args.set_host
    if args.set_port:
        config["Client"]["port"] = args.set_port
    with open(f"{current_dir}/client.conf", "w") as configfile:
        config.write(configfile)

    if not args.host:
        args.host = config["Client"]["host"]
    if not args.port:
        args.port = config["Client"]["port"]
    return args


def start(screen, host, port):
    asyncio.run(main(screen, host, port))


async def main(screen, host, port):
    try:
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ssl_cert = ssl.get_server_certificate((host, port))
        ssl_context.load_verify_locations(cadata=ssl_cert)
    except ssl.SSLError:
        ssl_context = None

    async with websockets.connect(
        f"wss://{host}:{port}", ping_interval=None, ssl=ssl_context
    ) as websocket:
        await console.run(screen, websocket)


if __name__ == "__main__":
    current_dir = pathlib.Path(__file__).parent
    if not pathlib.Path(f"{current_dir}/client.conf").exists():
        create_config()
    config = read_config(current_dir)
    args = load_args(config, current_dir)

    try:
        curses.wrapper(start, args.host, args.port)
    except ConnectionRefusedError:
        print("Cannot connect to server, make sure it is running")
