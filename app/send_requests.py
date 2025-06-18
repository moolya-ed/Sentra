import requests
import time
from datetime import datetime

# Configuration
base_url = "http://localhost:8000/traffic/log"
source_ip = "192.168.1.250"
total_requests = 105  # Change if you want more

payload = {
    "source_ip": source_ip,
    "method": "GET",
    "url": "/products",
    "headers": "{}",
    "user_agent": "sqlmap",
    "request_size": 123,
    "response_code": 200,
    "response_time_ms": 50
}

for i in range(1, total_requests + 1):
    response = requests.post(base_url, json=payload)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        if response.status_code == 200:
            data = response.json()
            alerts = data.get("alerts_triggered", [])
            if alerts:
                alerts_str = alerts
            else:
                alerts_str = "None"
            status_text = "200 OK"
        elif response.status_code == 403:
            alerts_str = "IP Blocked"
            status_text = "403 Forbidden"
        else:
            alerts_str = "Unknown"
            status_text = f"{response.status_code}"
    except Exception as e:
        alerts_str = f"Error parsing JSON"
        status_text = f"{response.status_code}"

    print(f"Request #{i} | IP: {source_ip} | Time: {timestamp} | Status: {status_text} | Alerts: {alerts_str}")

    time.sleep(0.1)  # Optional pause
