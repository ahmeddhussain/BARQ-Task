# AI usage disclosure

- **Tool/model:**  Claude/ Google AI Studio
- **Purpose:** Brainstorming architecture, Log Analysis, designing scripts, and drafting documentation.
- **Files or decisions affected:** 
  - `docker-compose.yml` overall understanding of the architecture.
  - `validate.py`, `failure_test.py`, `backup.sh`, `restore.sh` (Implementation logic)
  - `log_analysis.md` (Regex and `jq` query optimization)
  - `.github/workflows.ci` Create dummy/Test Environment Variables for CI Testing

- **What you changed or rejected:** 
  - `docker-compose.yml` drafting, did it manually to ensure secure architecture.
  - Rewrote the technical `decisions.md` and `Troubleshooting.md` to accurately reflect personal troubleshooting decisions rather than claiming credit.
  - Corrected pipe streaming logic in `restore.sh` on failure.
  

- **How you independently verified it:** 
  - Executed every Linux/bash command manually in local terminal.
  - Ran unit tests (`python -m unittest discover -s tests -v`) to verify application semantics.
  - Confirmed all automated checks passed via independent GitHub Actions workflow runs.
  - Manual review on starting and before submission for all files.

- **Related commits:** Across all progressive commits in the repository history.