# Log analysis

## 1. What UTC interval is covered? How many valid, malformed and duplicate lines are in each file?
- **Interval:** 2026-08-20 11:00:00 UTC to 11:29:57 UTC (approx. 30 minutes).
- **Counts:**
  - `access.log`: 726 total lines. 1 malformed line , 5 exact duplicate lines , 720 distinct client requests. Total 725 valid lines.
  - `application.log`: 730 total lines. 1 malformed line , 2 exact duplicate lines, 727 valid entries (includes both `http_request` and `dependency_error` events).
  - `error.log`: 68 lines. 68 valid NGINX error strings, 0 malformed, 0 duplicates.
### Commands Used

#### 1. Check the log interval

```bash
head -n 1 logs/access.log && tail -n 1 logs/access.log
```

**Output:**

```text
{"timestamp":"2026-08-20T11:00:00.015Z","request_id":"lab-000001","method":"GET","path":"/missing","status":404,"upstream":"172.23.0.11:8080","upstream_status":"404","request_time":0.015,"client":"192.0.2.24"}
{"timestamp":"2026-08-20T11:29:57.578Z","request_id":"lab-000720","method":"GET","path":"/","status":200,"upstream":"172.23.0.12:8080","upstream_status":"200","request_time":0.078,"client":"192.0.2.24"}
```

#### 2. Count total log lines

```bash
wc -l logs/*.log
```

**Output:**

```text
  726 logs/access.log
  730 logs/application.log
   68 logs/error.log
 1524 total
```

#### 3. Find duplicate lines

**Access log:**

```bash
sort logs/access.log | uniq -cd
```

**Application log:**

```bash
sort logs/application.log | uniq -cd
```

**Access Log Output:**

```text
2 {"timestamp":"2026-08-20T11:05:00.055Z","request_id":"lab-000121","method":"GET","path":"/","status":200,"upstream":"172.23.0.11:8080","upstream_status":"200","request_time":0.055,"client":"192.0.2.24"}
2 {"timestamp":"2026-08-20T11:10:00.015Z","request_id":"lab-000241","method":"GET","path":"/","status":200,"upstream":"172.23.0.11:8080","upstream_status":"200","request_time":0.015,"client":"192.0.2.24"}
2 {"timestamp":"2026-08-20T11:15:00.055Z","request_id":"lab-000361","method":"GET","path":"/","status":200,"upstream":"172.23.0.11:8080","upstream_status":"200","request_time":0.055,"client":"192.0.2.24"}
2 {"timestamp":"2026-08-20T11:20:00.015Z","request_id":"lab-000481","method":"GET","path":"/","status":200,"upstream":"172.23.0.11:8080","upstream_status":"200","request_time":0.015,"client":"192.0.2.24"}
2 {"timestamp":"2026-08-20T11:25:00.055Z","request_id":"lab-000601","method":"GET","path":"/","status":200,"upstream":"172.23.0.11:8080","upstream_status":"200","request_time":0.055,"client":"192.0.2.24"}
```

**Application log duplicates:**

```text
2 {"timestamp": "2026-08-20T11:07:30.035Z", "level": "INFO", "event": "http_request", "request_id": "lab-000181", "instance_id": "app-01", "method": "GET", "path": "/", "status": 200, "duration_ms": 35.0}
2 {"timestamp": "2026-08-20T11:17:30.035Z", "level": "INFO", "event": "http_request", "request_id": "lab-000421", "instance_id": "app-01", "method": "GET", "path": "/", "status": 200, "duration_ms": 35.0}
```

#### 4. Find malformed / non-JSON lines

**Access log:**

```bash
grep -v '}$' logs/access.log
```

**Application log:**

```bash
grep -v '}$' logs/application.log
```

**Output:**

```text
{"timestamp":"2026-08-20T11:12:48Z","request_id":

{"timestamp":"2026-08-20T11:17:00Z","event":
```


## 2. How many distinct client requests occurred? How did you deduplicate?
- **Distinct Requests:** 720 total distinct client `request_id`s (from lab-000001 to lab-000720).
- **Deduplication:** Extracted the `.request_id` field using `jq -R 'fromjson? | .request_id'`. The `fromjson?` operator safely catches and suppresses the malformed JSON line on line 313. Piped the IDs through `sort -u` to deduplicate retried requests and double-printed lines.
- **Commands used:**
  ```bash
  jq -R 'fromjson? | .request_id' logs/access.log | sort -u | grep -v '^null$' | wc -l
  ```

## 3. What are the final client status counts and error rate?
- **Counts:** 
  - `200 OK`: 620 requests
  - `404 Not Found`: 10 requests
  - `502 Service Unavailable`: 40 requests
  - `503 Service Unavailable`: 47 requests
  - `504 Gateway Timeout`: 8 requests
- **Error Rate:** 
  - Total Server Errors (502 + 503 + 504) = 95 errors.
  - Using Total Valid Responses (725) as denominator: 95 / 725 = 13.10% error rate.
  - Using Distinct Client Requests (720) as denominator: 95 / 720 = 13.19% error rate.
- **Commands used:**
  ```bash
  # Gets the final status for each unique request ID
  jq -R 'fromjson? | .status' logs/access.log | grep -v '^null$' | sort | uniq -c
  ```

## 4. Which paths, time windows and backends account for the failures?
- **502 Bad Gateway:** Occurred between 11:05:02 and 11:09:57 UTC. Caused exclusively by `app-02` (172.23.0.12:8080) crashing and returning `"Connection refused"`.

- **503 Service Unavailable:**
  - 11:12:09 - 11:15:52 UTC: Occurred on `/ready and /counter` paths across both backends due to Redis connection timeouts.
  - 11:20:07 - 11:21:45 UTC: Occurred on `/ready and /records` paths across both backends due to PostgreSQL authentication failures (InvalidPassword).

- **504 Gateway Timeout:** Occurred between 11:25:14 and 11:26:47 UTC exclusively on `/records` across both backends, caused by PostgreSQL queries locking/hanging past NGINX's 2-second timeout threshold.


## 5. What are the median and p95 client latencies?
- **Method:**  Extracted `request_time` (units: seconds) across all valid `access log` lines, sorted numerically, and extracted the 50th percentile (Median) and 95th percentile (p95) using awk.
- **Median:** 0.054 seconds (54 ms).
- **p95:** 2.001 seconds (2,001 ms)
- **Commands used:**
  ```bash
  jq -R 'fromjson? | .request_time' logs/access.log | grep -v '^null$' | sort -n | awk '{all[NR] = $0} END{print "Median: " all[int(NR*0.50)] "s\np95: " all[int(NR*0.95)] "s"}'

  ```

## 6. Which requests retried upstream? How many succeeded after retrying?
- **Retries:**  `19 requests` triggered an upstream failover/retry (detected by checking for multiple comma-separated entries in .upstream).
- **Successes:** `19 out of 19 (100%)` succeeded on their second attempt, returning an upstream status of 502, 200 and delivering a final 200 OK to the client.
- **Commands used:**
  ```bash
  # Total retries
  jq -R 'fromjson? | select(.upstream | contains(",")) | .request_id' logs/access.log | sort -u | grep -v '^null$' | wc -l

  # Succeeded on retry (contains 200)
  jq -R 'fromjson? | select(.upstream | contains(",")) | .upstream_status' logs/access.log | grep -c '200'  
  ```

## 7. Build an incident timeline
- **11:00:00 - 11:05:00 UTC:** Normal, baseline operations across both backends.
- **11:05:02 - 11:09:57 UTC (App Outage):** app-02 crashes. error.log reports connect() failed (111: Connection refused) for 172.23.0.12:8080. NGINX attempts failover; 19 requests fail over to app-01 and succeed, while non-retried requests receive 502s.
- **11:12:09 - 11:15:52 UTC (Cache Outage):** Redis stops responding. application.log shows TimeoutError on dependency=redis. Endpoints /counter and /ready return 503s.
- **11:20:07 - 11:21:45 UTC (Database Auth Outage):** PostgreSQL rejects connections. application.log shows InvalidPassword on dependency=postgres. Endpoints /records and /ready return 503s.
- **11:25:14 - 11:26:47 UTC (Database Lockup):** PostgreSQL hangs. Requests to /records stall. error.log reports upstream timed out (110: Operation timed out). Clients receive 504 Gateway Timeout after 2.001s.
- **11:27:00 - 11:30:00 UTC:** System returns to normal health

## 8. Show one correlated failed request and one successful request.
- **Correlated Successful Request:** `lab-000002`
  - `access.log`: `{"timestamp":"2026-08-20T11:00:02.532Z","request_id":"lab-000002","path":"/health","status":200,"upstream":"172.23.0.12:8080","request_time":0.032}`
  - `application.log`: `{"timestamp": "2026-08-20T11:00:02.532Z", "level": "INFO", "event": "http_request", "request_id": "lab-000002", "instance_id": "app-02", "status": 200, "duration_ms": 32.0}`
- **Correlated Failed Request:** `lab-000484` (Dependency Failure)
  - `access.log`: `{"timestamp":"2026-08-20T11:20:07.541Z","request_id":"lab-000484","path":"/ready","status":503,"upstream":"172.23.0.12:8080"}`
  - `application.log`: 
    1. `{"timestamp": "2026-08-20T11:20:07.540Z", "level": "ERROR", "event": "dependency_error", "request_id": "lab-000484", "dependency": "postgres", "error_type": "InvalidPassword"}`
    2. `{"timestamp": "2026-08-20T11:20:07.541Z", "level": "WARN", "event": "http_request", "request_id": "lab-000484", "status": 503, "duration_ms": 41.0}`

## 9. Which errors appear to be proxy/connectivity vs application issues?
- **Proxy/Connectivity:** The `502 Connection refused` and `504 Gateway Timeout` errors are NGINX/Proxy errors. They appear in `error.log` and mean NGINX either couldn't reach the container or the container hung up.
- **Application/Dependency:** The `503 Service Unavailable` errors are Application logic. They do *not* appear in NGINX `error.log` because NGINX successfully reached the Flask app, and the Flask app intentionally replied with a 503 `dependency error` (InvalidPassword, TimeoutError) due to Redis/Postgres failing.

## 10. What do the logs not prove? What would you check next?
- **What they do not prove:** The logs show the *symptoms* (a container refused connections, passwords failed, queries timed out), but they do not prove the *root cause* on the host infrastructure. For example, they do not prove whether `app-02` crashed due to an Out-Of-Memory (OOM) kill by the Linux kernel, a segmentation fault, or an accidental container stop. They also don't prove whether the Redis timeout was caused by high network packet loss or high CPU utilization on the Redis container.
- **What to check next:**
  1. Inspect container exit codes and termination reasons: `docker inspect app-02 --format='{{.State.ExitCode}}`.
  2. Inspect the raw engine logs for PostgreSQL and Redis: `docker compose logs postgres redis`.
  3. Inspect host-level kernel and hardware metrics: `dmesg -T` for OOM events, and monitoring dashboards for CPU/Memory/Disk I/O spikes.



