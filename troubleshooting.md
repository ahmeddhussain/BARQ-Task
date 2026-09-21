# Troubleshooting journal

## Entry 1 / 20.9.2026 3:00PM /Foundation Networking and Healthchecks
- Symptom: App containers stay in `(health: starting)` or become `unhealthy`. NGINX cannot route traffic to them as they are mounted to `APP_HOST= "127.0.01"` which stays inside the container. Both backend containers return the same instance ID.
- Hypothesis: Docker's healthcheck command is pointing to the wrong endpoint. The Flask app is binding to the loopback interface preventing external container communication. The environment variables for app-02 were copy-pasted incorrectly.
- Command or test: `docker compose ps` and checking `app/server.py` routes.
- Actual output: `app-01` showed `unhealthy`. `server.py` showed `@app.get("/health")` not `/healthz`.
- Failed attempt and what changed your thinking: None yet; initial static analysis revealed the misconfigurations.
- Root cause: `APP_HOST` set to `127.0.0.1`, healthcheck requesting `/healthz`, and `app-02` INSTANCE_ID hardcoded to `app-01`.
- Fix: In `docker-compose.yml`, updated APP_HOST to `0.0.0.0`, changed healthcheck URL to `/health`, and updated app-02 instance ID to `app-02`.
- Retest evidence: `docker compose ps` now shows both apps as `(healthy)`.
- Related commit: [main a1fd7b7] fix(app): bind app to 0.0.0.0, correct healthcheck endpoint, and fix app-02 identity
- Remaining uncertainty: Can NGINX actually reach them now? We need to verify NGINX routing next.

## Entry 2 / 20.9.2026 3:15 PM / NGINX Routing and Ports
- Symptom: Unable to reach the application via host port 8080 and If reachable which is not, half the requests would fail with 502 Bad Gateway.
- Hypothesis: NGINX port mapping in Docker is mismatched with the NGINX config. Upstream load balancing has the wrong port for app-01.
- Command or test: `curl -i http://localhost:8080/`
- Actual output: curl: (56) Recv failure: Connection reset by peer
- Failed attempt and what changed your thinking: N/A.
- Root cause: `docker-compose.yml` mapped host to port 81, but `nginx.conf` listens on port 80. `nginx.conf` routed app-01 traffic to port 8081 instead of 8080.
- Fix: Fixed compose ports to `"8080:80"`. Fixed `nginx.conf` upstream to `app-01:8080`. 
- Retest evidence: `curl http://localhost:8080/` now returns a 200 response with alternating instance IDs.
- Related commit: [main 61873bd] fix(nginx): correct host port mapping and upstream load balancing ports
- Remaining uncertainty: The application is reachable, but are the database and cache functioning?

## Entry 3 / 20.9.2026 3:25 PM /Database Connectivity and Security
- Symptom: `curl http://localhost:8080/ready` returns a `503 error` and `unready`, indicating Postgres and Redis are unavailable to the application.
- Hypothesis: The application's database connection strings have incorrect credentials or ports. Furthermore, the databases are exposing ports to the host machine, violating security requirements stated by the instructions.
- Command or test: `curl http://localhost:8080/ready` and comparing `config/app.env` with `docker-compose.yml`.
- Actual output: 503 Service Unavailable.
- Failed attempt and what changed your thinking: N/A.
- Root cause: `app.env` contained incorrect ports (5433, 6380) and an incorrect Postgres password ending in `8d` instead of `8c`.
- Fix: Updated `app.env` to use standard ports (5432, 6379) and correct password. Removed `ports` declarations for postgres and redis from `docker-compose.yml` to ensure network isolation.
- Retest evidence: `curl http://localhost:8080/ready` now returns 200 OK and reports both dependencies as "ready".
- Related commit: [main 31b1f30] fix(db): correct connection credentials and isolate database ports
- Remaining uncertainty: Data persistence. If we restart the Postgres container, does it keep our records?

## Entry 4 / 20.9.2026 3:35 PM / Data Persistence and Volume Mounting
- Symptom: Data written to Postgres (/records) and Redis (/counter) is lost when the respective containers are restarted.
- Hypothesis: The containers are not properly configured with persistent Docker volumes mapping to their default data directories.
- Command or test: `curl` POST to `/records`, `docker compose restart postgres`, and `curl` GET to `/records`.
- Actual output: The newly created record disappeared after restart.
- Failed attempt and what changed your thinking: N/A.
- Root cause: Postgres was configured to use a `tmpfs` RAM disk for `/var/lib/postgresql/data` and the named volume was mapped to a `/backup` folder. Redis was launched with command flags explicitly disabling persistence (`--save ""` and `--appendonly "no"`).
- Fix: Removed Postgres `tmpfs`, mapped `postgres-data` volume to `/var/lib/postgresql/data`. Changed Redis command to `--appendonly yes`, mapped a new `redis-data` volume to `/data`, and added `redis-data` to the global volumes block.
- Retest evidence: Records and counters now successfully survive container restarts.
- Related commit: [main d267a07] fix(storage): enable proper volume persistence for Postgres and Redis
- Remaining uncertainty: Environment variables and secrets are still hard-copied into the Docker image, violating security rules.

## Entry 5 / 20.9.2026 4:15 PM / Security: Container Privilege and Secrets Management
- Symptom: Static analysis of the repository reveals security vulnerabilities violating best practices.
- Hypothesis: The Dockerfile runs the application as root and copies secrets into the image. The compose file hardcodes database passwords.
- Command or test: Inspected `Dockerfile` and `docker-compose.yml`.
- Actual output: `USER root` and `COPY config/app.env` present in Dockerfile. `POSTGRES_PASSWORD` in plain text in compose file.
- Failed attempt and what changed your thinking: N/A.
- Root cause: Intentional security misconfigurations by the developers.
- Fix: Removed `.env` COPY command from Dockerfile and changed user to `app`. Moved the Postgres password to `config/app.env` and injected it into the postgres container using `env_file` in compose.
- Retest evidence: `docker compose build && docker compose up -d` successfully builds and runs. Environment remains healthy running as a non-privileged user without exposed secrets.
- Related commit: [main 8d27ac7] refactor(security): run app as non-root user and secure plain-text secrets
- Remaining uncertainty: We still need to configure resource limits, restart policies, secrets protection and Block direct NGINX access to PostgreSQL/Redis.

## Entry 6 / 21.9.2026 1:45 PM /roduction Readiness: Isolation, Limits, and Secrets
- Symptom: NGINX had unnecessary access to the backend network. Containers lacked automatic restart policies and resource limits. Secret file `config/app.env` was not properly ignored by Git or Docker.
- Hypothesis: The infrastructure lacked production-hardening configurations as mandated by the requirements.
- Command or test: Inspected `docker-compose.yml`, `.gitignore`, and `.dockerignore`.
- Actual output: NGINX attached to `backend`. `restart: "no"` set on apps. `config/app.env` missing from ignore lists.
- Failed attempt and what changed your thinking: N/A.
- Root cause: Missing production safeguards in the baseline code.
- Fix: Removed `backend` network from NGINX. Changed restart policies to `always` for all services. Added CPU (0.5) and Memory (256M) limits to the apps. Appended `config/app.env` to `.gitignore` and `.dockerignore`.
- Retest evidence: `docker compose up -d` successfully applies limits and network constraints. Containers remain healthy.
- Related commit:[main e9c939e] feat(infra): harden networks, add resource limits, set restart policies and ignore secrets
- Remaining uncertainty: Environment is stable. Ready to begin Part 3 (Automated Validation and Scripts).

**Note**: `./screenshots` shows commands output, debugging and analysis along side with this documentation.

