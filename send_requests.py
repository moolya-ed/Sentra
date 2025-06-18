import requests
import time

url = "http://localhost:8000/traffic/log"

payload = {
    "source_ip": "192.168.1.250",
    "method": "GET",
    "url": "/products",
    "headers": "{}",
    "user_agent": "sqlmap",
    "request_size": 150,
    "response_code": 200,
    "response_time_ms": 100
}

for i in range(1, 101):
    r = requests.post(url, json=payload)
    print(f"➡️ Sent request #{i} | Status: {r.status_code}")

    try:
        data = r.json()
        print(f"↪️  Response: {data}")

        if data.get("alerts_triggered"):
            print(f"⚠️ ALERT Triggered: {data['alerts_triggered']}")
    except Exception as e:
        print(f"❌ JSON parse error: {e}")

    time.sleep(0.1)
