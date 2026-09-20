# Troubleshooting journal

Keep chronological entries. Copy this block for each meaningful investigation.

## Entry / date / time
- Symptom:
- Hypothesis:
- Command or test:
- Actual output:
- Failed attempt and what changed your thinking:
- Root cause:
- Fix:
- Retest evidence:
- Related commit:
- Remaining uncertainty:

Do not fabricate a failed attempt just to fill the template. Record actual attempts.


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
- Related commit: [main 61873bd] fix(nginx): correct host port mapping and upstream load balancing port
- Remaining uncertainty: Data persistence. If we restart the Postgres container, does it keep our records?


