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
- Remaining uncertainty: Can NGINX actually reach them now? We need to verify NGINX routing next.

