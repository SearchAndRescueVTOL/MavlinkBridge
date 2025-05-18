import subprocess
import os
import time

LOG_DIR = "/tmp/mavlink_logs"
session_name = "mavwatch"


def get_log_files():
    return [
        os.path.join(LOG_DIR, f)
        for f in sorted(os.listdir(LOG_DIR))
        if f.endswith(".log")
    ]


def tmux_cmd(*args):
    subprocess.run(["tmux"] + list(args), check=True)


def setup_tmux_session():
    # Kill old session if it exists
    subprocess.run(
        ["tmux", "kill-session", "-t", session_name], stderr=subprocess.DEVNULL
    )

    # Wait until at least one log exists
    files = get_log_files()
    while not files:
        print("[INFO] No logs yet — waiting 1s for first message...")
        time.sleep(1)
        files = get_log_files()

    first_log = files[0]

    # Create a new session with the first log
    tmux_cmd("new-session", "-d", "-s", session_name, "tail", "-f", first_log)

    # Add other logs as new panes
    for log_path in files[1:]:
        tmux_cmd("split-window", "-t", session_name, "-v", "tail", "-f", log_path)
        tmux_cmd("select-layout", "-t", session_name, "tiled")

    # Attach immediately
    tmux_cmd("attach-session", "-t", session_name)


if __name__ == "__main__":
    setup_tmux_session()

