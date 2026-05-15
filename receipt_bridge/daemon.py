import socket
import logging
import signal
import sys
import configparser
from pathlib import Path

from .printer import Printer

DLE = 0x10
EOT = 0x04

log = logging.getLogger("receipt_bridge")

CONFIG_PATH = Path("/etc/receipt-bridge/config.conf")

_DEFAULTS = {
    "daemon": {"port": "9100", "bind": "0.0.0.0"},
    "printer": {"device": "auto", "baud_rate": "115200"},
}

# Returned to the client when a status read times out (printer OK, no errors, paper present).
_FALLBACK_STATUS = b"\x12"


def load_config(path: Path = CONFIG_PATH) -> configparser.ConfigParser:
    cfg = configparser.ConfigParser()
    cfg.read_dict(_DEFAULTS)
    if path.exists():
        cfg.read(path)
    return cfg


def _handle_client(conn: socket.socket, printer: Printer) -> None:
    addr = conn.getpeername()
    log.info("client connected: %s", addr)

    # Three-state machine that detects DLE EOT <n> status query sequences
    # embedded in the ESC/POS byte stream and routes the 1-byte printer
    # response back to the TCP client. Everything else is buffered and
    # written to the printer in chunks.
    state = "NORMAL"  # NORMAL | SAW_DLE | SAW_EOT
    print_buf = bytearray()

    def flush():
        if print_buf:
            printer.write(bytes(print_buf))
            print_buf.clear()

    try:
        while True:
            data = conn.recv(4096)
            if not data:
                break

            for byte in data:
                if state == "NORMAL":
                    if byte == DLE:
                        state = "SAW_DLE"
                    else:
                        print_buf.append(byte)

                elif state == "SAW_DLE":
                    if byte == EOT:
                        flush()
                        state = "SAW_EOT"
                    else:
                        # DLE followed by a non-EOT byte is ordinary print data
                        print_buf.append(DLE)
                        print_buf.append(byte)
                        state = "NORMAL"

                elif state == "SAW_EOT":
                    # byte is the status subcommand (0x01–0x04)
                    query = bytes([DLE, EOT, byte])
                    log.debug("status query 0x%02x", byte)
                    printer.write(query)
                    response = printer.read(1)
                    if response:
                        log.debug("status response 0x%02x", response[0])
                        conn.sendall(response)
                    else:
                        log.warning("status read timed out, returning fallback")
                        conn.sendall(_FALLBACK_STATUS)
                    state = "NORMAL"

            # Flush whatever print data accumulated this recv
            if state == "NORMAL":
                flush()

    except OSError as e:
        log.warning("connection error (%s): %s", addr, e)
    finally:
        flush()
        conn.close()
        log.info("client disconnected: %s", addr)


def run(config_path: Path = CONFIG_PATH) -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    cfg = load_config(config_path)
    port = cfg.getint("daemon", "port")
    bind = cfg.get("daemon", "bind")
    raw_device = cfg.get("printer", "device")
    baud = cfg.getint("printer", "baud_rate")

    device = None if raw_device == "auto" else raw_device
    printer = Printer(device=device, baud_rate=baud)
    printer.open()

    def _shutdown(sig, _frame):
        log.info("caught signal %s, shutting down", sig)
        printer.close()
        sys.exit(0)

    signal.signal(signal.SIGTERM, _shutdown)
    signal.signal(signal.SIGINT, _shutdown)

    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((bind, port))
    srv.listen(1)  # queue depth 1 — single-client printer
    log.info("listening on %s:%d  printer=%s", bind, port, printer.device)

    try:
        while True:
            conn, _ = srv.accept()
            _handle_client(conn, printer)
    finally:
        srv.close()
        printer.close()
