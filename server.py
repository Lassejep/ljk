#!/usr/bin/env python3
import asyncio
import logging
import pickle
import pathlib
import ssl
import argparse
import functools
from websockets.server import serve
from websockets.exceptions import ConnectionClosedOK
from datetime import datetime
from os import path, mkdir
from src import db, handlers
import configparser


async def handler(ws, database):
    lhost, lport = ws.local_address
    logging.info(f"Connected to {lhost}:{lport}")
    while True:
        try:
            msg = await ws.recv()
            rhost, rport = ws.remote_address
            msg = pickle.loads(msg)
            logging.info(f"{rhost}:{rport} sent command {msg['command']}")
        except ConnectionClosedOK:
            logging.info(f"{rhost}:{rport} disconnected")
            break
        except Exception as e:
            logging.error(f"{rhost}:{rport} error: {e}")
            break

        match msg["command"]:
            case "register":
                await handlers.register_user(ws, msg, database, rhost, rport)
            case "auth":
                await handlers.auth(ws, msg, database, rhost, rport)
            case "get_vaults":
                await handlers.get_vaults(ws, msg, database, rhost, rport)
            case "get_vault":
                await handlers.get_vault(ws, msg, database, rhost, rport)
            case "save_vault":
                await handlers.save_vault(ws, msg, database, rhost, rport)
            case "create_vault":
                await handlers.create_vault(ws, msg, database, rhost, rport)
            case "delete_vault":
                await handlers.delete_vault(ws, msg, database, rhost, rport)
            case "change_email":
                await handlers.change_email(ws, msg, database, rhost, rport)
            case "change_auth_key":
                await handlers.change_auth_key(ws, msg, database, rhost, rport)
            case "delete_account":
                await handlers.delete_account(ws, msg, database, rhost, rport)
            case "update_vault_key":
                await handlers.update_vault_key(
                    ws, msg, database, rhost, rport
                )
            case "update_vault_name":
                await handlers.update_vault_name(
                    ws, msg, database, rhost, rport
                )
            case _:
                await handlers.invalid_command(ws, msg, rhost, rport)


async def db_backup(database, backup_dir, backup_interval, max_backups):
    if int(backup_interval) == 0:
        return
    while True:
        await asyncio.sleep(3600 * int(backup_interval))
        if int(max_backups) != 0:
            try:
                backups = sorted(
                    pathlib.Path(backup_dir).iterdir(), key=path.getmtime
                )
                if len(backups) > int(max_backups):
                    for backup in backups[:-int(max_backups)]:
                        backup.unlink()
            except Exception as e:
                logging.error(f"Backup cleanup error: {e}")
        try:
            await database.backup(backup_dir)
        except Exception as e:
            logging.error(f"Backup error: {e}")


async def run_server(host, port, ssl_context, database):
    bound_handler = functools.partial(handler, database=database)
    async with serve(
        bound_handler, host, port,
        logger=logging.getLogger(),
        ssl=ssl_context,
        ping_interval=None
    ):
        await asyncio.Future()


def create_config():
    config = configparser.ConfigParser()
    current_dir = pathlib.Path(__file__).parent
    config["server"] = {
        "host": "0.0.0.0",
        "port": "5050",
        "ssl_path": "",
        "log_dir": f"{current_dir}/logs",
        "database": f"{current_dir}/users.db",
        "backup_dir": f"{current_dir}/backups",
        "backup_interval": "6",
        "max_backups": "10"
    }
    with open(f"{current_dir}/server.conf", "w") as configfile:
        config.write(configfile)


def load_config(current_dir):
    config = configparser.ConfigParser()
    config.read(f"{current_dir}/server.conf")
    return config


def arg_parser():
    parser = argparse.ArgumentParser(description="Password Manager Server")
    parser.add_argument(
        "--set-database",
        metavar="PATH",
        help="Set the path to the database"
    )
    parser.add_argument(
        "--set-host",
        metavar="HOST",
        help="Set the host to listen on"
    )
    parser.add_argument(
        "--set-port",
        metavar="PORT",
        help="Set the port to listen on"
    )
    parser.add_argument(
        "--set-ssl-cert",
        metavar="PATH",
        help="Set the path to the SSL certificate"
    )
    parser.add_argument(
        "--set-log-dir",
        metavar="PATH",
        help="Set the path to the log directory"
    )
    parser.add_argument(
        "--set-backup-dir",
        metavar="PATH",
        help="Set the path to the backup directory"
    )
    parser.add_argument(
        "--set-backup-interval",
        metavar="HOURS",
        help="Set the backup interval in hours if set to 0 no backups"
    )
    parser.add_argument(
        "--set-max-backups",
        metavar="NUM",
        help="Set the maximum number of backups if set to 0 no limit"
    )
    args = parser.parse_args()
    return args


def load_args(current_dir, config):
    args = arg_parser()
    if args.set_database is not None:
        config["server"]["database"] = args.set_database
    if args.set_host is not None:
        config["server"]["host"] = args.set_host
    if args.set_port is not None:
        config["server"]["port"] = args.set_port
    if args.set_ssl_cert is not None:
        config["server"]["ssl_path"] = args.set_ssl_cert
    if args.set_log_dir is not None:
        config["server"]["log_dir"] = args.set_log_dir
    if args.set_backup_dir is not None:
        config["server"]["backup_dir"] = args.set_backup_dir
    if args.set_backup_interval is not None:
        config["server"]["backup_interval"] = args.set_backup_interval
    if args.set_max_backups is not None:
        config["server"]["max_backups"] = args.set_max_backups
    with open(f"{current_dir}/server.conf", "w") as configfile:
        config.write(configfile)


def main(
    host, port, ssl_context, db_path, backup_dir, backup_interval, max_backups
):
    database = db.Database(db_path)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    tasks = [
        loop.create_task(run_server(host, port, ssl_context, database)),
        loop.create_task(db_backup(
            database, backup_dir, backup_interval, max_backups
        ))
    ]
    loop.run_until_complete(asyncio.wait(tasks))
    loop.close()


if __name__ == "__main__":
    current_dir = pathlib.Path(__file__).parent
    if not path.exists(f"{current_dir}/server.conf"):
        create_config()
        print("Configuration file created")
    config = load_config(current_dir)
    load_args(current_dir, config)
    if not path.exists(config["server"]["log_dir"]):
        mkdir(config["server"]["log_dir"])
    if not path.exists(config["server"]["backup_dir"]):
        mkdir(config["server"]["backup_dir"])
    if config["server"]["ssl_path"] != "":
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ssl_context.load_cert_chain(config["server"]["ssl_path"])
    else:
        ssl_context = None
    timestamp = datetime.now().strftime("%Y-%m-%d")
    logging.basicConfig(
        filename=f"{config['server']['log_dir']}/{timestamp}.log",
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s"
    )

    print(
        f"Listening on {config['server']['host']}:{config['server']['port']}"
    )
    print(f"Database File: {config['server']['database']}")
    print(f"Log File: {config['server']['log_dir']}/{timestamp}.log")
    if ssl_context is not None:
        print("SSL enabled")
    else:
        print("SSL disabled")
    print("Press Ctrl+C to stop")

    running = True
    while running:
        try:
            main(
                config["server"]["host"],
                int(config["server"]["port"]),
                ssl_context,
                config["server"]["database"],
                config["server"]["backup_dir"],
                config["server"]["backup_interval"],
                config["server"]["max_backups"]
            )
        except KeyboardInterrupt:
            print("Stopping server")
            running = False
