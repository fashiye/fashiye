import time
import secrets


def generate_order_no():
    timestamp = str(int(time.time() * 1000))
    random_part = ''.join(secrets.choice('0123456789') for _ in range(4))
    return f"BO{timestamp}{random_part}"
