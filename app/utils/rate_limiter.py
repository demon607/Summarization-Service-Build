import time
from collections import defaultdict

request_log: dict[str, list[float]] = defaultdict(list)
MAX_REQUESTS = 10
TIME_WINDOW_HOURS = 1
TIME_WINDOW_SECONDS = TIME_WINDOW_HOURS * 3600


def is_rate_limited(ip_address: str) -> bool:
    """Check if an IP address is rate-limited."""
    current_time = time.time()
    request_timestamps = request_log.get(ip_address, [])
    valid_timestamps = [
        ts for ts in request_timestamps if current_time - ts < TIME_WINDOW_SECONDS
    ]
    request_log[ip_address] = valid_timestamps
    if len(valid_timestamps) >= MAX_REQUESTS:
        return True
    request_log[ip_address].append(current_time)
    return False