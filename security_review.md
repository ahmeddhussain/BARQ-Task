
# Security and production-readiness review

## 1. Container running as root
- Risk and evidence: Dockerfile ended with `USER root`.
- Impact: High. If the Flask app is compromised via Remote Code Execution, the attacker gains root privileges inside the container, making container escape easier.
- Implemented fix: Changed `USER root` to `USER app` in the Dockerfile.
- Production follow-up: Enforce a Kubernetes PodSecurityPolicy blocking all root containers.
- How to verify: Run `docker exec app-01 whoami` and ensure it returns `app`.

## 2. Secrets baked into Docker Image
- Risk and evidence: Dockerfile contained `COPY config/app.env /srv/app.env`.
- Impact: Critical. Anyone pulling the image from the registry can extract the plaintext database passwords.
- Implemented fix: Removed the `COPY` line from the Dockerfile. Secrets are now injected at runtime.
- Production follow-up: Use a secret manager (HashiCorp Vault, AWS Secrets Manager) and inject secrets directly into memory or ESO via Kubernetes.
- How to verify: Inspect the image layers using `docker history barq-assessment-app-01` to ensure `app.env` is not copied.

## 3. Hardcoded Passwords in Compose File
- Risk and evidence: `docker-compose.yml` contained `POSTGRES_PASSWORD: BarqLabOnly_7qN2vK8c` in plain text.
- Impact: Critical. The password was tracked in Git history, exposing it to anyone with repository access.
- Implemented fix: Moved the password to `config/app.env` and used `env_file:` in the compose configuration.
- Production follow-up: Implement pre-commit hooks (like `git-secrets` or `trufflehog`) to block commits containing high-entropy strings or known credential patterns.
- How to verify: Read `docker-compose.yml` and ensure no `PASSWORD` fields exist.

## 4. Unignored Secret Files
- Risk and evidence: `config/app.env` was missing from `.gitignore` and `.dockerignore`.
- Impact: High. The local secrets file could accidentally be pushed to GitHub or sent to the Docker build context.
- Implemented fix: Appended `config/app.env` to both `.gitignore` and `.dockerignore`.
- Production follow-up: Keep `.env.example` heavily documented but completely free of real values.
- How to verify: Run `git status` after modifying `config/app.env` to ensure Git ignores it.

## 5. Exposed Backend Database Ports
- Risk and evidence: `docker-compose.yml` mapped Postgres and Redis ports to the host (e.g., `15432:5432`).
- Impact: High. Bypasses the NGINX firewall, allowing direct host-level access to the databases.
- Implemented fix: Removed the `ports` blocks from `postgres` and `redis` services.
- Production follow-up: Place databases in private cloud subnets with strict Security Groups allowing ingress only from the application tier.
- How to verify: Run `docker compose ps` and verify no host ports are listed for the DB containers.

## 6. NGINX over-privileged network access
- Risk and evidence: NGINX was attached to both `frontend` and `backend` networks.
- Impact: Medium. A vulnerability in NGINX could be exploited to scan or attack the database directly.
- Implemented fix: Removed `backend` from the NGINX networks list.
- Production follow-up: Implement strictly defined Network Policies to block unauthorized East-West traffic.
- How to verify: Run `docker inspect nginx` and verify it is only attached to the frontend network.

## 7. Temporary Filesystem Data Loss
- Risk and evidence: Postgres was mounted with `tmpfs: [/var/lib/postgresql/data]`.
- Impact: Critical (Availability). All user records were permanently deleted whenever the container restarted.
- Implemented fix: Removed `tmpfs` and mapped a named Docker volume to the data directory.
- Production follow-up: Implement automated daily snapshots and cross-region replication for disaster recovery.
- How to verify: Save a record, run `docker compose restart postgres`, and fetch the records to ensure survival.

## 8. Redis explicitly disabling persistence
- Risk and evidence: Redis command was `redis-server --save "" --appendonly no`.
- Impact: Medium (Data Loss). The `/counter` metric would reset to zero on restart.
- Implemented fix: Changed command to `--appendonly yes` and mounted a `redis-data` volume.
- Production follow-up: Depending on business requirements, consider if cache persistence is actually required, or if volatile cache is acceptable to save disk I/O.
- How to verify: Increment the counter, restart Redis, and check the counter again.