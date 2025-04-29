import os
import re
from pymavlink import mavutil

LOG_DIR = "/tmp/mavlink_logs"
os.makedirs(LOG_DIR, exist_ok=True)

def sanitize_tag(tag):
    return re.sub(r'[^A-Za-z0-9_]', '_', tag)

def extract_tag_and_msg(text):
    match = re.match(r'\[([A-Z0-9_]+)\]\s+(.*)', text)
    if match:
        return sanitize_tag(match.group(1)), match.group(2)
    return "UNKNOWN", text

def start_listener():
    mav = mavutil.mavlink_connection("udp:0.0.0.0:14550")
    print("[MAVLINK] Listening on 0.0.0.0:14550")

    while True:
        msg = mav.recv_match(type="STATUSTEXT", blocking=True)
        if msg and hasattr(msg, "text"):
            try:
                text = msg.text.strip('\x00')
                tag, content = extract_tag_and_msg(text)

                log_path = os.path.join(LOG_DIR, f"{tag}.log")
                with open(log_path, "a") as f:
                    f.write(content + "\n")

                print(f"[{tag}] {content}")
            except Exception as e:
                print(f"[ERROR] {e}")

