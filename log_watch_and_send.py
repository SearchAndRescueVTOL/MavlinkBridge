import os
import time
import threading
from send_mavlink import init_mavlink, send_statustext

# Mutex for MAVLink send operation
mavlink_lock = threading.Lock()

def watch_log_file(filepath: str, tag: str, poll_interval: float = 0.5):
    """
    Watch a single log file and send new lines via MAVLink with a thread-safe lock.

    Args:
        filepath (str): The path to the log file.
        tag (str): The tag/prefix for MAVLink messages.
        poll_interval (float): How often to poll the file (in seconds).
    """
    if not os.path.exists(filepath):
        print(f"[{tag}] File not found: {filepath}")
        return

    print(f"[{tag}] Watching {filepath}")

    with open(filepath, 'r') as file:
        file.seek(0, os.SEEK_END)  # skip existing content

        while True:
            line = file.readline()
            if line:
                clean_line = line.strip()
                if clean_line:
                    with mavlink_lock:
                        try:
                            send_statustext(clean_line, program_id=tag)
                            print(f"[{tag}] {clean_line}")
                        except Exception as e:
                            print(f"[{tag}] Failed to send MAVLink message: {e}")
            else:
                time.sleep(poll_interval)

def start_watchers(file_tag_pairs):
    """
    Starts a thread for each log file to be watched.

    Args:
        file_tag_pairs (list of tuples): Each tuple is (filepath, tag).
    """
    threads = []

    for filepath, tag in file_tag_pairs:
        thread = threading.Thread(target=watch_log_file, args=(filepath, tag), daemon=True)
        thread.start()
        threads.append(thread)

    for t in threads:
        t.join()

if __name__ == "__main__":
    init_mavlink()

    # Define log files and tags
    file_tag_pairs = [
        ("/home/sarv-pi/ROS_Jazz_ws/src/ros_image_2_gps/xrce_agent.log", "XRCE"),
        ("/home/sarv-pi/TRIGGER_GPS_LOGS/output.txt", "IR"),
        ("/home/sarv-pi/RGBCapture/rgbcapture.log", "RGB"),
        ("/home/sarv-pi/FLIR-Capture/C-GStreamer/HardwarePiGpioTriggerLogOutput.txt", "ROS")
    ]

    start_watchers(file_tag_pairs)

