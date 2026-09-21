
# BARQ Systems - DevOps Internship Assessment

An automated, hardened, and highly available microservice deployment consisting of a Flask API load-balanced across two instances by NGINX, backed by persistent PostgreSQL storage and Redis caching.

---

## Architecture Overview

```
[ Client / Browser ] 
        │ (Host Port 8080)
        ▼
┌────────────────────────────────────────────────────────┐
│                      NGINX                             │
│       (Reverse Proxy & Round-Robin Load Balancer)      │
└───────────────┬────────────────────────┬───────────────┘
                │                        │
         frontend network         frontend network
                │                        │
                ▼                        ▼
     ┌────────────────────┐    ┌────────────────────┐
     │  Flask (app-01)    │    │  Flask (app-02)    │
     │  Non-root (app)    │    │  Non-root (app)    │
     └──────────┬─────────┘    └─────────┬──────────┘
                │                        │
         backend network          backend network
                │                        │
        ┌───────┴────────────────────────┴───────┐
        ▼                                        ▼
┌──────────────────┐                    ┌──────────────────┐
│    PostgreSQL    │                    │      Redis       │
│  (postgres-data) │                    │   (redis-data)   │
└──────────────────┘                    └──────────────────┘
```

- **Frontend Network:** Connects NGINX to `app-01` and `app-02`.
- **Backend Network:** Connects `app-01` and `app-02` to PostgreSQL and Redis. NGINX is isolated from the backend network.
- **Port Exposure:** Only NGINX port 8080 is published to the host. Direct host access to application and database ports is strictly blocked.

---

## Quickstart & Operational Commands

### 1. Prerequisites & Environment Setup
Copy the environment template and ensure credentials are set:
```bash
cp .env.example .env
mkdir -p config
cat << 'EOF' > config/app.env
DATABASE_URL=postgresql://barq_postgres:5432
REDIS_URL=ahmed_redis://redis:6379/0
POSTGRES_PASSWORD=AhmedPASS
EOF
```
**Note** Those are dummy `.env.example` values not real values, for the app to work you will need real values from `./config/app.env`.

### 2. Build and Start
Build the hardened non-root images and launch the environment:
```bash
docker compose build
docker compose up -d
```

Check service health:
```bash
docker compose ps
```

### 3. Verification & Testing
Run the automated environment validation script (tests endpoints, load balancing, port isolation, and dependencies):
```bash
./validate.py
```

Run the resilience and failure test (proves failover and zero-downtime recovery when a backend container stops):
```bash
./failure_test.py
```

### 4. Disaster Recovery (Backup & Restore)
Create a logical PostgreSQL backup:
```bash
./backup.sh
```

Restore the latest backup from `backups/`:
```bash
./restore.sh
```

### 5. Stop and Cleanup
Gracefully stop the environment without destroying persistent volumes:
```bash
docker compose down
```

To completely destroy containers and wipe persistent data:
```bash
docker compose down -v
```

---

## Assessment Questions & Answers

### 1. What failed first? What proved the cause? Which failed attempt taught you something?
- **What failed first:** The application containers failed their Docker healthchecks, remaining in an `unhealthy` state.
- **What proved the cause:** `docker compose ps` showed `unhealthy`. Inspecting `docker-compose.yml` revealed the healthcheck pinged `/healthz`, while `app/server.py` defines `@app.get("/health")`.
- **What a failed attempt taught:** During backup/restore testing, running `docker exec -i postgres pg_restore ... "$FILE"` failed because the container searched for the file in its own internal filesystem. Piping input using shell redirection (`< "$FILE"`) streamed the host backup directly into the container's standard input.

### 2. What patterns did the logs reveal? How did you avoid double-counting requests?
- **Patterns:** The logs revealed three distinct historical failures: an NGINX proxy failure due to `app-02` crashing (11:05), application dependency timeouts due to Redis failing (11:12), and database authentication failures on PostgreSQL (11:20).
- **Avoiding double-counting:** I filtered logs by unique `request_id` values using `jq -R 'fromjson? | .request_id' | sort -u`. The `fromjson?` filter was essential to prevent parser crashes on corrupted/malformed log lines.

### 3. How do requests flow? Why these ports, networks, and readiness checks?
- **Flow:** Client ➔ NGINX:8080 (host) ➔ NGINX:80 (container) ➔ Round-Robin upstream to `app-01:8080` or `app-02:8080` ➔ PostgreSQL:5432 / Redis:6379.
- **Why these networks:** Least-privilege architecture. NGINX only exists on the `frontend` network; databases only exist on the `backend` network. If the reverse proxy is compromised, the attacker cannot pivot directly into PostgreSQL.
- **Why readiness checks:** `/ready` evaluates real TCP/SQL connectivity to both database backends before considering the container capable of handling traffic.

### 4. Why these timeouts, retries, restart settings, and resource limits?
- **Timeouts & Retries:** NGINX is configured with `proxy_connect_timeout 2s;` and upstream retry logic so that a dead backend instance fails over to the healthy instance within milliseconds, preventing client-facing 502 errors.
- **Restart Policies:** `restart: always` guarantees that containers recover automatically from unexpected process crashes or host reboots.
- **Resource Limits:** Applied CPU (`0.5`) and Memory (`256M`) limits prevent a buggy application instance from starving the host or other containers (Noisy Neighbor mitigation).

### 5. When should validation fail? What does green CI prove, or not prove?
- **When validation fails:** `validate.py` fails immediately if any required endpoint returns non-200/201, if dependency readiness reports unavailable, if load balancing fails to cycle through both backends, or if any database port is exposed to the host.
- **What Green CI proves:** Proves that code builds in a clean environment, configurations are syntactically valid, containers pass health checks, and endpoints comply with the API contract.
- **What Green CI does not prove:** It does not prove application performance under heavy concurrent load, cross-region latency, or resilience against physical host hardware failure.

### 6. Which single points of failure remain? How would you fix them in production?
- **Single Points of Failure:** 
  1. NGINX is a single container. If the host or NGINX container dies, traffic halts.
  2. PostgreSQL is a single master container. If the database crashes or on backup script, state cannot be written.
- **Production Fixes:**
  1. Deploy multiple NGINX instances behind a cloud load balancer (e.g., AWS ALB or Cloudflare).
  2. Migrate PostgreSQL to a managed multi-AZ service (e.g., AWS RDS) with automated failover and read replicas.
```

