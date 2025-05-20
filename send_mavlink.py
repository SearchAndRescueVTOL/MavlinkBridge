from pymavlink import mavutil
import time

# Global MAVLink connection object
_mavlink_conn = None

def init_mavlink(gcs_ip="172.31.100.102", gcs_port=14541, system_id=2, component_id=200):
    """
    Initializes the MAVLink connection if not already initialized.
    """
    global _mavlink_conn
    if _mavlink_conn is None:
        _mavlink_conn = mavutil.mavlink_connection(
            f'udpout:{gcs_ip}:{gcs_port}',
            source_system=system_id,
            source_component=component_id
        )
        _mavlink_conn.mav.heartbeat_send(
            mavutil.mavlink.MAV_TYPE_ONBOARD_CONTROLLER,
            mavutil.mavlink.MAV_AUTOPILOT_INVALID,
            0, 0, 0
        )
        print(f"[MAVLINK] Initialized to {gcs_ip}:{gcs_port}")

def is_mavlink_initialized():
    return _mavlink_conn is not None

def send_statustext(message: str, program_id: str = "UNKNOWN", severity: int = 6):
    """
    Sends a STATUSTEXT message with a prefix like [BAT], [NAV], etc.

    Args:
        message (str): The actual log message.
        program_id (str): Short tag like 'NAV', 'BAT', etc.
        severity (int): MAV_SEVERITY level (default 6 = INFO).
    """
    global _mavlink_conn
    if not _mavlink_conn:
        raise RuntimeError("MAVLink not initialized. Call init_mavlink() first.")

    prefix = f"[{program_id}]"
    if prefix == "[RGB]" or prefix == "[IR]":
        message = message[33:75]
    else:
        message = message[:50]
    full_message = f"{prefix} {message}"[:50]
    padded = full_message.encode('utf-8')
    if len(padded) < 50:
        padded += b'\x00' * (50 - len(padded))
    else:
        padded = padded[:50]

    _mavlink_conn.mav.statustext_send(severity, padded)

if __name__ == "__main__":
	init_mavlink()
	while not is_mavlink_initialized():
		print("failed to initialized")
		init_mavlink()
		time.sleep(1)

	while True:
		send_statustext("mavlink sending!")
		time.sleep(1)
