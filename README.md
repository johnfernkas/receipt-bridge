# receipt-bridge

A small daemon that exposes a USB-connected Epson TM-T88V receipt printer as a TCP socket (port 9100) on a Raspberry Pi Zero W. Any ESC/POS client on the network can connect and send raw print data. DLE EOT status queries are detected in the byte stream, forwarded to the printer, and the response is returned to the client — enabling paper-sensor support in clients that use it.

## Architecture

```
ESC/POS client
  │  raw ESC/POS → TCP :9100
  ▼
Pi Zero W (receipt-bridge daemon)
  │  /dev/ttyUSB0 or /dev/usb/lp0
  ▼
Epson TM-T88V
```

## Status query support (paper sensor)

The TM-T88V responds to `DLE EOT <n>` (0x10 0x04 0x0n) queries with a single status byte. `receipt-bridge` detects these sequences in the byte stream, routes them to the printer, and forwards the response back to the client.

**Important:** bidirectional I/O requires the printer to be in **USB-Serial mode** so it appears as `/dev/ttyUSB0`. The USB printer class driver (`/dev/usb/lp0`) is write-only on Linux and cannot return status bytes. To switch modes, enter the TM-T88V self-test menu and change the USB mode setting.

## Installation

```bash
git clone <this-repo>
cd receipt-bridge
sudo bash install.sh
sudo nano /etc/receipt-bridge/config.conf   # adjust device path if needed
sudo systemctl start receipt-bridge
sudo journalctl -u receipt-bridge -f
```

## Configuration

`/etc/receipt-bridge/config.conf`:

```ini
[daemon]
port = 9100
bind = 0.0.0.0

[printer]
device = auto        # or /dev/ttyUSB0 / /dev/usb/lp0
baud_rate = 115200
```

`device = auto` tries `/dev/usb/lp0`, `/dev/ttyUSB0`, `/dev/ttyACM0` in that order.

## Running manually

```bash
python3 -m receipt_bridge                         # uses /etc/receipt-bridge/config.conf
python3 -m receipt_bridge /path/to/config.conf    # custom config
```

## Troubleshooting

| Symptom | Fix |
|---|---|
| `no printer device found` | Check `ls /dev/usb/lp*` and `ls /dev/ttyUSB*`; set `device =` explicitly |
| Status queries time out | Switch printer to USB-Serial mode so `/dev/ttyUSB0` appears |
| Permission denied on device | Add your user to `lp` (for lp0) or `dialout` (for ttyUSB0) groups |
| Client cannot connect | Confirm port 9100 is reachable: `nc -zv <pi-ip> 9100` |
