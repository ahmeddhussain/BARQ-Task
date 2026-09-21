
# Technical decisions

## Decision 1: Healthcheck Tool Selection
- Choice: Retained the built-in Python `urllib.request` for the Docker healthcheck, only updating the endpoint from `/healthz` to `/health`.
- Why: The baseline used `urllib`. While fixing the endpoint, I had to decide whether to keep `urllib` or switch to `curl`. I chose to keep `urllib` because it requires no extra installations.
- Alternative: Install `curl` or `wget` in the Dockerfile.
- Trade-off: Adding `curl` increases the Docker image size and introduces a new potential attack surface, whereas Python's standard library is already present and sufficient for liveness probing.
- Evidence / commit: `docker-compose.yml` healthcheck command utilizes `python -c`.
- Production improvement: Move to a dedicated orchestration tool (like Kubernetes) that natively handles HTTP liveness and readiness probes without needing shell commands.

## Decision 2: Network Isolation Implementation
- Choice: Removed NGINX from the `backend` Docker network entirely.
- Why: To satisfy the requirement to "Block direct NGINX access to PostgreSQL/Redis", I had to choose how to enforce it. Removing the network attachment at the Docker daemon level is more secure than trying to write NGINX routing rules to block traffic.
- Alternative: Keep NGINX on both networks but use `nginx.conf` rules (like `deny all;`) for database ports.
- Trade-off: Application-layer blocking relies on perfect configuration and is prone to human error. Network-layer isolation is enforced by the host OS.
- Evidence / commit: `docker-compose.yml` -> `nginx` service -> `networks` only lists `frontend`.
- Production improvement: Implement strict egress firewall rules or a Service Mesh to control container-to-container communication.

## Decision 3: Secrets Injection Method
- Choice: Used the `env_file` directive in Compose to pass database credentials.
- Why: The baseline had hardcoded passwords. I had to decide how to pass them securely. Using `env_file: ./config/app.env` keeps the compose file clean and prevents secrets from leaking into Git history.
- Alternative: Define the variables directly under the `environment:` block using shell substitution (e.g., `POSTGRES_PASSWORD: ${DB_PASS}`).
- Trade-off: Shell substitution requires the user running the command to have exported the variable in their terminal beforehand. `env_file` centralizes it and is easier for local development.
- Evidence / commit: `postgres` service in `docker-compose.yml` uses `env_file: ./config/app.env`.
- Production improvement: Use a native secrets manager like HashiCorp Vault or AWS Secrets Manager with ESO instead of local `.env` files.

## Decision 4: Resource Limit Values
- Choice: Set application resource limits to `0.5` CPUs and `256M` of memory.
- Why: The PDF required resource limits but did not specify the exact values. Because this is a lightweight Flask/API application doing simple DB reads/writes, 256MB is more than enough.
- Alternative: Set higher limits (e.g., `1GB` RAM) or no limits at all.
- Trade-off: Setting limits too low causes Out-Of-Memory (OOM) crashes. Setting no limits allows a single container to starve the host. 256MB is a safe, conservative baseline for a small Python microservice.
- Evidence / commit: `deploy.resources` block under `x-app` in `docker-compose.yml`.
- Production improvement: Implement load testing (e.g., Locust or JMeter) to profile the exact memory usage under heavy load, and adjust the limits accordingly.

## Decision 5: Storage Persistence Strategy
- Choice: Used Docker "Named Volumes" (`postgres-data` and `redis-data`) for database persistence.
- Why: The baseline used a volatile `tmpfs` RAM disk. To fix data loss, I chose Named Volumes because they are fully managed by the Docker daemon.
- Alternative: Host bind mounts (e.g., `- ./local_data:/var/lib/postgresql/data`).
- Trade-off: Bind mounts expose the data directly to the host filesystem, which can cause severe read/write permission issues depending on whether the host is Linux, Mac, or Windows (WSL). Named volumes abstract this away and "just work" across all OS types.
- Evidence / commit: `volumes` block at the bottom of `docker-compose.yml`.
- Production improvement: Mount network-attached storage (like AWS EBS) or migrate entirely to managed database services (like AWS RDS) for automated backups and scaling.
