#!/usr/bin/env python3
import os
import re
import time
import argparse
from pymavlink import mavutil

LOG_DIR = "/tmp/mavlink_logs"
os.makedirs(LOG_DIR, exist_ok=True)


def sanitize_tag(tag):
    return re.sub(r"[^A-Za-z0-9_]", "_", tag)


def extract_tag_and_msg(text):
    match = re.match(r"\[([A-Z0-9_]+)\]\s+(.*)", text)
    if match:
        return sanitize_tag(match.group(1)), match.group(2)
    return "UNKNOWN", text


class MAVLinkShell:
    def __init__(self, conn_str, baud, devnum, debug=False):
        self.debug = debug
        self.devnum = devnum
        self.mav = mavutil.mavlink_connection(conn_str, autoreconnect=True, baud=baud)
        # send and await heartbeat
        self.mav.mav.heartbeat_send(
            mavutil.mavlink.MAV_TYPE_GENERIC,
            mavutil.mavlink.MAV_AUTOPILOT_INVALID,
            0,
            0,
            0,
        )
        self.mav.wait_heartbeat()
        if self.debug:
            print("[MAVShell] Heartbeat OK")

    def send_cmd(self, cmd: str):
        """Send raw command via SERIAL_CONTROL."""
        if not cmd.endswith("\n"):
            cmd += "\n"
        payload = cmd.encode("utf-8")
        offset = 0
        while offset < len(payload):
            chunk = payload[offset : offset + 70]
            offset += len(chunk)
            buf = list(chunk) + [0] * (70 - len(chunk))
            flags = (
                mavutil.mavlink.SERIAL_CONTROL_FLAG_EXCLUSIVE
                | mavutil.mavlink.SERIAL_CONTROL_FLAG_RESPOND
            )
            self.mav.mav.serial_control_send(self.devnum, flags, 0, 0, len(chunk), buf)
            if self.debug:
                print(f"[MAVShell] Sent {chunk!r}")

    def read_responses(self, timeout=1.0):
        """
        Collect STATUSTEXT messages for `timeout` seconds,
        return a list of (TAG, line) tuples.
        """
        end = time.time() + timeout
        out = []
        while time.time() < end:
            msg = self.mav.recv_match(type="STATUSTEXT", blocking=True, timeout=0.1)
            if not msg or not hasattr(msg, "text"):
                continue
            text = msg.text.strip("\x00")
            tag, line = extract_tag_and_msg(text)
            out.append((tag, line))
        return out

    def interactive(self):
        print("mavsh> ", end="", flush=True)
        try:
            while True:
                line = input().strip()
                if line in ("exit", "quit"):
                    break

                # send it off
                self.send_cmd(line)
                # give PX4 a moment
                time.sleep(0.05)
                # collect any STATUSTEXT
                replies = self.read_responses(timeout=1.0)
                if not replies:
                    print("(no response)")
                for tag, text in replies:
                    # log by tag
                    logf = os.path.join(LOG_DIR, f"{tag}.log")
                    with open(logf, "a") as f:
                        f.write(text + "\n")
                    print(f"[{tag}] {text}")
                print("mavsh> ", end="", flush=True)
        except KeyboardInterrupt:
            print("\n[+] Exiting shell.")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="MAVLink NSH shell client")
    p.add_argument(
        "-p",
        "--port",
        default="udp:0.0.0.0:14445",
        help="MAVLink connection (udp:// or /dev/tty)",
    )
    p.add_argument(
        "-b", "--baud", type=int, default=57600, help="Serial baud (if using serial)"
    )
    p.add_argument(
        "-d", "--devnum", type=int, default=10, help="PX4 SERIAL_CONTROL port number"
    )
    p.add_argument("--debug", action="store_true")
    args = p.parse_args()

    shell = MAVLinkShell(args.port, args.baud, args.devnum, args.debug)
    shell.interactive()
