
# BARQ Systems — DevOps Internship Assessment (Final Production State)

[![CI Pipeline](https://github.com/ahmeddhussain/BARQ-Task/actions/workflows/ci.yml/badge.svg)](https://github.com/ahmeddhussain/BARQ-Task/actions)
![Docker](https://img.shields.io/badge/Docker-24.0+-blue.svg)
![Compose](https://img.shields.io/badge/Compose-v2-blue.svg)
![Python](https://img.shields.io/badge/Python-3.12-yellow.svg)
![NGINX](https://img.shields.io/badge/NGINX-1.28-green.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue.svg)
![Redis](https://img.shields.io/badge/Redis-7.4-red.svg)

This repository contains the hardened, containerized deployment of the BARQ Systems assessment service. The final production solution features an NGINX reverse proxy load-balancing traffic across **three non-root Flask API instances** on **public host port 8090**, backed by persistent PostgreSQL storage and Redis in-memory caching with strict network-level isolation.

---

## Table of Contents
1. [Architecture & Request Flow](#architecture--request-flow)
2. [Network & Port Security Matrix](#network--port-security-matrix)
3. [Environment Configuration](#environment-configuration)
4. [Quickstart & Operations Playbook](#quickstart--operations-playbook)
5. [Validation & Automated Testing](#validation--automated-testing)
6. [Disaster Recovery (Backup & Restore)](#disaster-recovery-backup--restore)
7. [API Contract Reference](#api-contract-reference)
8. [Comprehensive Evaluation Answers](#comprehensive-evaluation-answers)

---

## Architecture & Request Flow

The final production system operates on **port 8090** with three dynamically balanced compute nodes:

```
                      [ External Client / Traffic ]
                                    │
                                    │ HTTP Requests
                                    ▼
       ┌─────────────────────────────────────────────────────────┐
       │                       Host Gateway                      │
       │                   Published Port: 8090                  │
       └────────────────────────────┬────────────────────────────┘
                                    │
                              frontend net
                                    │
                                    ▼
       ┌─────────────────────────────────────────────────────────┐
       │                       NGINX Edge                        │
       │               Container Port: 80 (TCP)                  │
       │           Reverse Proxy & Load Balancer                 │
       │      Upstream Pool: app-01, app-02, and app-03          │
       └───────┬────────────────────┬────────────────────┬───────┘
               │                    │                    │
  frontend net │       frontend net │       frontend net │
               ▼                    ▼                    ▼
       ┌───────────────┐    ┌───────────────┐    ┌───────────────┐
       │ Flask: app-01 │    │ Flask: app-02 │    │ Flask: app-03 │
       │ User: app     │    │ User: app     │    │ User: app     │
       │ Port: 8080    │    │ Port: 8080    │    │ Port: 8080    │
       │ 0.5c / 256MB  │    │ 0.5c / 256MB  │    │ 0.5c / 256MB  │
       └───────┬───────┘    └───────┬───────┘    └───────┬───────┘
               │                    │                    │
   backend net │        backend net │        backend net │
               └────────────────────┼────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    ▼                               ▼
       ┌─────────────────────────┐     ┌─────────────────────────┐
       │       PostgreSQL        │     │          Redis          │
       │       Version 16        │     │       Version 7.4       │
       │  Internal Port: 5432    │     │  Internal Port: 6379    │
       │  Volume: postgres-data  │     │  Volume: redis-data     │
       │  Mount: .../data        │     │  Persistence: AOF (yes) │
       └─────────────────────────┘     └─────────────────────────┘
```

### Network Isolation Policy
- **`frontend` Network (`bridge`):** Bridges NGINX and application backends (`app-01`, `app-02`, and `app-03`). Isolated from persistence infrastructure.
- **`backend` Network (`bridge`, `internal: true`):** Connects compute instances to PostgreSQL and Redis. NGINX has zero network interfaces connected to the backend network, preventing lateral traversal or direct database penetration.

---

## Network & Port Security Matrix

| Service | Container Name | Internal Port | Host Published Port | Network Membership | User Privilege |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Edge Proxy** | `nginx` | 80/tcp | **`8090`** | `frontend` | `nginx` |
| **API Node 1** | `app-01` | 8080/tcp | *Blocked* | `frontend`, `backend` | `app` (UID 10001) |
| **API Node 2** | `app-02` | 8080/tcp | *Blocked* | `frontend`, `backend` | `app` (UID 10001) |
| **API Node 3** | `app-03` | 8080/tcp | *Blocked* | `frontend`, `backend` | `app` (UID 10001) |
| **Database** | `postgres` | 5432/tcp | *Blocked* | `backend` | `postgres` |
| **Cache Store** | `redis` | 6379/tcp | *Blocked* | `backend` | `redis` |

---

## Environment Configuration

Configuration is managed via runtime environment injection. Secrets are untracked by Git (`.gitignore`) and excluded from Docker build contexts (`.dockerignore`).

---

## Quickstart & Operations Playbook

All commands are copy-pasteable and must be executed from the repository root.

### 1. Initial Setup & Secrets Initialization
```bash
# Create local configuration file from template
mkdir -p config  #insert dummy info, real values should be in ./config/app.env
cat << 'EOF' > config/app.env
DATABASE_URL=postgresql://barq_postgres:5432
REDIS_URL=redis://ahmed_redis:6379/0
POSTGRES_PASSWORD=AhmedPASS
EOF

```

### 2. Build & Launch Stack (Port 8090)
```bash
# Build the non-root images using cache-safe syntax
docker compose build

# Launch the three-instance stack in detached mode
docker compose up -d

# Verify all 5 containers report healthy
docker compose ps
```

### 3. Verification & Live Traffic Balancing
```bash
# Validate that traffic distributes across all three instances
for i in {1..9}; do curl -s http://localhost:8090/instance | jq .instance_id; done
```

### 4. Stop & Teardown
```bash
# Graceful shutdown preserving persistent volumes
docker compose down

# Complete teardown purging volumes (destructive reset)
docker compose down -v
```

---

## Validation & Automated Testing

### 1. Automated Environment Validation
Verifies all public routes, proves upstream round-robin load distribution across all 3 nodes, tests readiness probing, and scans host network interfaces for unauthorized port leakage.
```bash
chmod +x validate.py
./validate.py 8090
```

### 2. Resilience & Chaos Engineering Test
Stops an active compute backend, measures continued traffic on healthy nodes alongside expected upstream timeout errors on the stopped node (due to `proxy_next_upstream off`), restores the stopped container, and proves recovery.
```bash
chmod +x failure_test.py
./failure_test.py
```

### 3. Application Unit Test Suite
Runs the internal test runner isolating Flask handlers with mock drivers:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m unittest discover -s tests -v
deactivate
```

---

## Disaster Recovery (Backup & Restore)

The persistence model relies on Docker Named Volumes backed by manual logical dump automation.

### Create Logical Backup
```bash
chmod +x backup.sh
./backup.sh
```
*Dumps PostgreSQL schema and table data into a binary custom-format `.dump` file located in `backups/`.*

### Restore Disaster Recovery Archive
```bash
chmod +x restore.sh
./restore.sh
```
*Identifies the latest backup archive, purges existing public schemas to prevent primary key collision, and restores data via input stream redirection.*

### Proof of Persistence Across Teardown
```bash
# 1. Insert test record on final port 8090
curl -H 'Content-Type: application/json' -d '{"title":"Disaster Recovery Verification"}' http://localhost:8090/records

# 2. Recreate containers keeping persistent volume
docker compose down
docker compose up -d
sleep 8

# 3. Prove persistence
curl http://localhost:8090/records
```

---

## API Contract Reference

| Method | Endpoint | Success Status | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/` | `200 OK` | Service liveness message and executing instance ID. |
| `GET` | `/health` | `200 OK` | Process liveness probe. Returns independent of dependencies. |
| `GET` | `/ready` | `200 OK` / `503` | Verifies live TCP/SQL queries against Postgres and Redis. |
| `GET` | `/instance` | `200 OK` | Returns backend identity (`app-01`, `app-02`, or `app-03`) for load balance testing. |
| `POST` | `/records` | `201 Created` | Inserts record into Postgres. Body: `{"title": "string"}`. |
| `GET` | `/records` | `200 OK` | Retrieves persisted records ordered by ID. |
| `GET` | `/counter` | `200 OK` | Atomically increments Redis key `barq:requests`. |

---

## Comprehensive Evaluation Answers

### 1. What failed first? What proved the cause? Which failed attempt taught you something?
- **Root Failure:** Application containers continuously failed startup checks, reporting `(health: starting)` before terminating as `unhealthy`.
- **Proof:** `docker compose ps` flagged unhealthiness. Cross-referencing `docker-compose.yml` (`/healthz`) with `app/server.py` (`/health`) proved an endpoint route mismatch. Furthermore, `APP_HOST` was bound to loopback `127.0.0.1`, physically preventing NGINX from bridging container boundaries.
- **Instructive Failure:** In `restore.sh`, executing `docker exec -i postgres pg_restore -U ... "$LATEST_BACKUP"` failed with `No such file or directory` because the command looked for the host-side file inside the container namespace. Switching to standard input streaming (`< "$LATEST_BACKUP"`) resolved the boundary crossing.

### 2. What patterns did the logs reveal? How did you avoid double-counting requests?
- **Patterns:** The historical logs recorded an application node crash (`app-02` at 11:05), an upstream cache timeout (Redis at 11:12), a database credential failure (Postgres at 11:20), and a table lockup causing 504 Gateway Timeouts (11:25).
- **Deduplication:** A corrupted line at line 313 in `access.log` caused naive JSON parsers to abort. Deduplication was executed using `jq -R 'fromjson? | .request_id' | sort -u`, parsing only valid JSON and isolating unique client request IDs.

### 3. How do requests flow? Why these ports, networks, and readiness checks?
- **Request Flow:** Client ➔ NGINX (Port 8090) ➔ Internal upstream balancing ➔ Flask (Port 8080) ➔ PostgreSQL (5432) & Redis (6379).
- **Network Design:** Strict dual-homed isolation. NGINX only has access to `frontend`; databases only exist on `backend`. The Flask compute layer acts as the bridge.
- **Readiness Checks:** `/ready` actively checks SQL execution (`SELECT 1`) and cache connectivity (`PING`). If a database drops, traffic is severed before user requests fail.

### 4. Why these timeouts, retries, restart settings, and resource limits?
- **Timeouts & Retries:** NGINX is configured with `proxy_connect_timeout 2s;` and `proxy_next_upstream off;`. When an instance stops, requests to the dead backend produce bounded 504 timeouts after 2 seconds, while requests to healthy instances continue to succeed with 200 OK.
- **Restart Policies:** `restart: always` ensures instant process recovery upon crashes or system reboots.
- **Resource Limits:** Restricting compute nodes to `0.5` CPU cores and `256MB` RAM guarantees that memory leaks or thread contention cannot induce kernel OOM panics on the host node.

### 5. When should validation fail? What does green CI prove, or not prove?
- **Failure Triggers:** `validate.py` fails if response latency exceeds bounded timeouts, dependencies are unreachable, load balancing is asymmetrical, or prohibited host ports are exposed.
- **What Green CI Proves:** Verifies automated build reproducibility, configuration syntax, non-root user permissions, and compliance with the API contract on a vanilla runner.
- **What Green CI Does Not Prove:** Does not prove zero-downtime rolling update safety, behavior under DDoS volumes, or underlying physical disk hardware longevity.

### 6. Which single points of failure remain? How would you fix them in production?
- **Single Points of Failure (SPOF):**
  1. *NGINX Edge Proxy:* A single NGINX container handles all ingress. If it fails, all routing stops.
  2. *PostgreSQL Master Node:* A single primary database instance without hot-standby replication.
- **Production Architecture Strategy:**
  1. Replace the single NGINX container with a Cloud Load Balancer (e.g., AWS Application Load Balancer) spanning multiple Availability Zones.
  2. Transition PostgreSQL to an automated multi-AZ cluster with synchronous replication and automated DNS failover (e.g., AWS RDS Multi-AZ).
