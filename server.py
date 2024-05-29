#!/usr/bin/env python3
import asyncio
import logging
import pickle
import pathlib
import ssl
import argparse
from websockets.server import serve
from websockets.exceptions import ConnectionClosedOK
from datetime import datetime
from os import path, mkdir
from src import db, handlers


async def handler(ws):
    database = db.Database(path_to_database)
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


async def main(host="0.0.0.0", port=8765, ssl_context=None):
    print(f"Listening on {args.host}:{args.port}")
    print(f"Database File: {args.database}")
    print(f"Log File: {logging.getLogger().handlers[0].baseFilename}")
    if ssl_context is not None:
        print("SSL enabled")
    else:
        print("SSL disabled")
    print("Press Ctrl+C to stop")

    async with serve(
        handler, host, port,
        logger=logging.getLogger(),
        ssl=ssl_context,
        ping_interval=None
    ):
        await asyncio.Future()

if __name__ == "__main__":
    current_dir = pathlib.Path(__file__).parent
    parser = argparse.ArgumentParser(description="Password Manager Server")
    parser.add_argument(
        "-d", "--database",
        default=path.join(current_dir, "users.db"),
        help="Path to the user database file"
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to listen on"
    )
    parser.add_argument(
        "-p", "--port",
        default=8765,
        help="Port to listen on"
    )
    parser.add_argument(
        "-s", "--ssl",
        default=None,
        help="Path to the SSL certificate"
    )
    parser.add_argument(
        "-l", "--log-dir",
        default=path.join(current_dir, "logs"),
        help="Path to the log directory"
    )
    parser.add_argument(
        "-t", "--test",
        action="store_true",
        default=False,
        help="Enable test mode"
    )
    args = parser.parse_args()

    if args.test:
        path_to_database = "/tmp/test.db"
        args.host = "0.0.0.0"
        args.port = 8765
        ssl_context = None
        logging.basicConfig(
            filename=f"{current_dir}/test.log",
            level=logging.INFO,
            format="%(asctime)s %(levelname)s %(message)s"
        )
    else:
        path_to_database = args.database
        if args.ssl is None:
            args.ssl = path.join(current_dir, "localhost.pem")
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ssl_context.load_cert_chain(args.ssl)
        timestamp = datetime.now().strftime("%Y-%m-%d")
        if not path.exists(args.log_dir):
            mkdir(args.log_dir)
        logging.basicConfig(
            filename=f"{args.log_dir}/{timestamp}.log",
            level=logging.INFO,
            format="%(asctime)s %(levelname)s %(message)s"
        )

    while True:
        try:
            asyncio.run(main(args.host, args.port, ssl_context))
        except KeyboardInterrupt:
            print("Stopping server")
            break
