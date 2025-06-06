import sqlite3
import os

DB_PATH = "db/traffic.db"

def init_db():
    os.makedirs("db", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS traffic_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_ip TEXT,
            source_port INTEGER,
            timestamp REAL,
            method TEXT,
            url TEXT,
            user_agent TEXT,
            request_size INTEGER,
            response_code INTEGER,
            response_time REAL
        )
    """)
    conn.commit()
    conn.close()

def log_request(source_ip, source_port, timestamp, method, url, user_agent, request_size, response_code, response_time):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO traffic_log (
            source_ip, source_port, timestamp, method, url, user_agent, request_size, response_code, response_time
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (source_ip, source_port, timestamp, method, url, user_agent, request_size, response_code, float(response_time)))
    conn.commit()
    conn.close()

def get_metrics():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*) FROM traffic_log
        WHERE timestamp >= strftime('%s', 'now', '-1 minute')
    """)
    requests_per_minute = cursor.fetchone()[0]

    cursor.execute("""
        SELECT source_ip, COUNT(*) as count FROM traffic_log
        GROUP BY source_ip ORDER BY count DESC LIMIT 5
    """)
    top_source_ips = [{"source_ip": row[0], "count": row[1]} for row in cursor.fetchall()]

    cursor.execute("SELECT method, COUNT(*) FROM traffic_log GROUP BY method")
    request_method_distribution = {row[0]: row[1] for row in cursor.fetchall()}

    cursor.execute("SELECT response_code, COUNT(*) FROM traffic_log GROUP BY response_code")
    response_code_statistics = {str(row[0]): row[1] for row in cursor.fetchall()}

    cursor.execute("""
        SELECT strftime('%M', datetime(timestamp, 'unixepoch')) as minute, COUNT(*)
        FROM traffic_log
        WHERE timestamp >= strftime('%s', 'now', '-1 hour')
        GROUP BY minute
        ORDER BY minute
    """)
    traffic_trend_last_hour = [{"minute": row[0], "count": row[1]} for row in cursor.fetchall()]

    cursor.execute("SELECT AVG(response_time) FROM traffic_log")
    avg_response_time = cursor.fetchone()[0] or 0

    conn.close()

    return {
        "requests_per_minute": requests_per_minute,
        "top_source_ips": top_source_ips,
        "request_method_distribution": request_method_distribution,
        "response_code_statistics": response_code_statistics,
        "traffic_trend_last_hour": traffic_trend_last_hour,
        "avg_response_time": avg_response_time
    }
