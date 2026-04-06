import time
import random


def generate_order_no():
    timestamp = str(int(time.time() * 1000))
    random_part = ''.join(random.choices('0123456789', k=4))
    return f"BO{timestamp}{random_part}"
