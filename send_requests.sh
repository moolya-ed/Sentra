#!/bin/bash

echo "🚀 Sending mixed requests to test detection + alerts"

for i in {1..120}
do
  if (( i % 40 == 0 )); then
    ip="192.168.1.250"  # spike + bot + sensitive URL
    ua="sqlmap"
    url="/admin"
  elif (( i % 20 == 0 )); then
    ip="192.168.1.$((RANDOM % 50 + 1))"
    ua="nmap"
    url="/products"
  else
    ip="192.168.1.$((RANDOM % 50 + 1))"
    ua="Mozilla/5.0"
    url="/products"
  fi

  response=$(curl -s -H "X-Forwarded-For: $ip" -X POST http://localhost:8000/traffic/log \
    -H "Content-Type: application/json" \
    -d "{\"source_ip\":\"$ip\",\"method\":\"GET\",\"url\":\"$url\",\"headers\":\"{}\",\"user_agent\":\"$ua\",\"request_size\":123,\"response_code\":200,\"response_time_ms\":50}")

  attack_type=$(echo "$response" | jq -r '.alerts_triggered | join("; ")')
  if [[ -z "$attack_type" || "$attack_type" == "null" || "$attack_type" == "" ]]; then
    attack_type="Normal"
  fi

  echo "#$i | IP=$ip | UA=$ua | URL=$url | ATTACK_TYPE=$attack_type"
done

