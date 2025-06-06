async function fetchMetrics() {
    try {
      const res = await fetch("http://localhost:8000/analysis/metrics");
      const data = await res.json();
  
      document.getElementById("rpm").innerText = data.requests_per_minute;
      document.getElementById("avg-resp-time").innerText = data.avg_response_time.toFixed(2);
  
      const ipsBody = document.querySelector("#top-ips-table tbody");
      ipsBody.innerHTML = "";
      data.top_source_ips.forEach(ip => {
        const row = document.createElement("tr");
        row.innerHTML = `<td>${ip.source_ip}</td><td>${ip.count}</td>`;
        ipsBody.appendChild(row);
      });
  
      const methodList = document.getElementById("method-dist");
      methodList.innerHTML = "";
      for (const [method, count] of Object.entries(data.request_method_distribution)) {
        const li = document.createElement("li");
        li.textContent = `${method}: ${count}`;
        methodList.appendChild(li);
      }
  
      const codeList = document.getElementById("resp-codes");
      codeList.innerHTML = "";
      for (const [code, count] of Object.entries(data.response_code_statistics)) {
        const li = document.createElement("li");
        li.textContent = `HTTP ${code}: ${count}`;
        codeList.appendChild(li);
      }
  
      const trendList = document.getElementById("trend");
      trendList.innerHTML = "";
      data.traffic_trend_last_hour.forEach(entry => {
        const li = document.createElement("li");
        li.textContent = `Minute ${entry.minute}: ${entry.count} reqs`;
        trendList.appendChild(li);
      });
  
    } catch (err) {
      console.error("Failed to fetch metrics", err);
    }
  }
  
  setInterval(fetchMetrics, 5000);
  fetchMetrics();
  