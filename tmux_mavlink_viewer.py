import subprocess
import os
import time

LOG_DIR = "/tmp/mavlink_logs"
session_name = "mavwatch"

def get_log_files():
    return [(os.path.join(LOG_DIR, f), f.replace(".log", "")) 
            for f in os.listdir(LOG_DIR) if f.endswith(".log")]

def tmux_cmd(*args):
    return subprocess.run(["tmux"] + list(args), check=True)

def setup_tmux_session():
    subprocess.run(["tmux", "kill-session", "-t", session_name], stderr=subprocess.DEVNULL)

    files = get_log_files()
    if not files:
        print("[INFO] No logs yet — waiting 1s for first message...")
        time.sleep(1)
        files = get_log_files()

    if not files:
        print("[ERROR] Still no logs — is mavlink_listener running?")
        return

    first_path, first_tag = files[0]
    tmux_cmd("new-session", "-d", "-s", session_name, "-n", first_tag, "tail", "-f", first_path)

    for path, tag in files[1:]:
        tmux_cmd("new-window", "-t", f"{session_name}:", "-n", tag, "tail", "-f", path)

    print(f"[✓] Tmux session '{session_name}' started with {len(files)} windows.")
    print(f"    Run: tmux attach-session -t {session_name}")

if __name__ == "__main__":
    setup_tmux_session()

