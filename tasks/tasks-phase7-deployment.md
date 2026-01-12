## Relevant Files

- `docker-compose.yml`
- `backend/app/tasks/maintenance.py` (New)

### Notes

- Even without full CI/CD, manual verification steps must be documented.
- Retention policy is crucial for compliance.

## Tasks

- [ ] 0.0 Create feature branch
  - [ ] 0.1 Create branch `feature/phase7-deploy`
- [ ] 1.0 UAT (User Acceptance Testing)
  - [ ] 1.1 Conduct sessions with RMs (Mobile responsiveness check).
  - [ ] 1.2 Verify Financial Ratio accuracy with Credit Analysts.
- [ ] 2.0 Security & PenTest
  - [ ] 2.1 Run `bandit` on backend code to check for Python vulnerabilities.
  - [ ] 2.2 Run `npm audit` on frontend.
- [ ] 3.0 Containerization
  - [ ] 3.1 Verify all services spin up correcty with `docker compose up --build`.
  - [ ] 3.2 Optimize Dockerfile sizing (multi-stage builds).
- [ ] 4.0 Retention Policy
  - [ ] 4.1 Create periodic task to archive/delete data > 7 years old.
