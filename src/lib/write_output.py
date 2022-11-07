import json

from datetime import datetime

def write_output(queue) -> int:
    start = datetime.now()
    end = datetime.now()
    return (end - start).seconds