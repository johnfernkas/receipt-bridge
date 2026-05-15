import os
import logging
import termios
from pathlib import Path
from typing import Optional

log = logging.getLogger("receipt_bridge")

CANDIDATE_DEVICES = ["/dev/usb/lp0", "/dev/ttyUSB0", "/dev/ttyACM0"]


def _is_serial(path: str) -> bool:
    return "tty" in path


class Printer:
    def __init__(self, device: Optional[str] = None, baud_rate: int = 115200):
        self.device = device or self._detect()
        self.baud_rate = baud_rate
        self._fd: Optional[int] = None

    def _detect(self) -> str:
        for path in CANDIDATE_DEVICES:
            if Path(path).exists():
                log.info("auto-detected printer device: %s", path)
                return path
        raise RuntimeError(
            f"no printer device found; tried: {CANDIDATE_DEVICES}. "
            "Set [printer] device in config."
        )

    def open(self) -> None:
        self._fd = os.open(self.device, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
        if _is_serial(self.device):
            self._configure_serial()
        else:
            # USB printer class: switch back to blocking writes, reads may time out
            flags = os.get_blocking(self._fd)
            os.set_blocking(self._fd, True)
        log.info("opened printer device: %s", self.device)

    def _configure_serial(self) -> None:
        baud_const = getattr(termios, f"B{self.baud_rate}", termios.B115200)
        iflag, oflag, cflag, lflag, _, _, cc = termios.tcgetattr(self._fd)

        iflag = termios.IGNPAR
        oflag = 0
        cflag = termios.CS8 | termios.CREAD | termios.CLOCAL
        lflag = 0
        cc[termios.VMIN] = 0
        cc[termios.VTIME] = 5  # 0.5 s read timeout

        termios.tcsetattr(
            self._fd,
            termios.TCSANOW,
            [iflag, oflag, cflag, lflag, baud_const, baud_const, cc],
        )
        os.set_blocking(self._fd, True)

    def write(self, data: bytes) -> None:
        if not data:
            return
        os.write(self._fd, data)

    def read(self, n: int) -> bytes:
        """Read up to n bytes. Returns b'' on timeout or error."""
        try:
            return os.read(self._fd, n)
        except BlockingIOError:
            return b""
        except OSError as e:
            log.warning("printer read error: %s", e)
            return b""

    def close(self) -> None:
        if self._fd is not None:
            try:
                os.close(self._fd)
            except OSError:
                pass
            self._fd = None

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, *_):
        self.close()
