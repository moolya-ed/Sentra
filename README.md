Sentra: Smart DDoS Detection System
✅ Project Overview

Sentra is a lightweight, FastAPI-based backend system for real-time DDoS detection and traffic monitoring.
It logs all HTTP requests, analyzes patterns, detects suspicious spikes, malicious bots, and sensitive URL access, and auto-blocks abusive IPs.

Key Features

    📊 Traffic Logging — Records IPs, methods, URLs, user-agents, headers, status codes.

    🚦 Anomaly Detection — Detects spikes, bad bots (sqlmap, nmap), and risky URLs (/admin, /etc/passwd).

    🔔 Alerting & Blocking — Generates alerts, auto-blocks IPs, and keeps an action log for auditing.

    📈 Analytics API — Summarizes traffic, top IPs, methods, recent alerts.

    🗃️ SQLite Database — Simple, portable, auto-creates tables.

    🐳 Dockerized — Easy to deploy with Docker Compose.


API Endpoints
Method	Endpoint	Description
GET	/system/status	Health check for API & DB
POST	/traffic/log	Log a new HTTP request
GET	/analytics/traffic-summary	Get traffic stats & recent alerts
GET	/blocked-ips	View currently blocked IPs
POST	/unblock-ip	Unblock a specific IP
GET	/admin/action-logs	View block/unblock history
GET	/admin/alerts	Get all stored alerts

 Detection Algorithms

Traffic Spike	Compares request count against threshold (e.g., 100/min).
Suspicious User-Agent	Checks user-agent for known bad signatures (sqlmap, nmap).
Sensitive URL Access	Blacklist match (e.g., /admin).

 How to Run

# Clone repo
git clone https://github.com/moolya-ed/Sentra.git
cd Sentra

# Start with Docker
docker compose up --build

📌 API Docs: http://localhost:8000/docs
✅ Testing

    Unit & integration tests for all sprints:

        tests/test_sprint1.py

        tests/test_sprint2.py

        tests/test_sprint3.py

        tests/test_sprint4.py

        tests/integration_all_sprints.py

# Run all tests
pytest tests/

📌 Most Valuable Byproduct

A robust, modular backend that logs & detects threats with real-time blocking.
Easy to extend with more detection rules or integrate with a frontend dashboard.

🔐 Note:
For security, do not commit .env with SMTP credentials.
Use environment variables or GitHub secrets for production.
