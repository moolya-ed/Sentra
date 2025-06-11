# sentra/app/utils.py

def calculate_request_size(headers: dict) -> int:
    return sum(len(k) + len(v) for k, v in headers.items())
