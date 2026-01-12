## Relevant Files

- `backend/app/services/alert_engine.py` (New) - Logic to check conditions.
- `backend/app/routers/company.py` (New) - Aggregation endpoints.
- `backend/app/middleware/audit.py` (New) - Logging middleware.

### Notes

- Alerts need to run efficiently. Maybe triggered post-ingestion or continuously managed by Celery Beat.
- "Company 360" is a read-heavy view; optimize queries.

## Tasks

- [x] 0.0 Create feature branch
  - [x] 0.1 Create branch `feature/phase5-backend`
- [x] 1.0 Alerting Engine
  - [x] 1.1 Implement rules engine (JSON logic evaluation).
  - [x] 1.2 Create "Check Alerts" task that runs after every ingestion/sentiment analysis.
  - [x] 1.3 Implement notification dispatch (Email/In-App).
- [x] 2.0 Company 360 Aggregator
  - [x] 2.1 Create API `GET /companies/{id}/overview` aggregating News, Sentiment, and Ratios.
  - [x] 2.2 Optimize with caching (Redis) for popular tickers.
- [x] 3.0 Audit Logging
  - [x] 3.1 Implement middleware to intercep requests to sensitive endpoints.
  - [x] 3.2 Log `user_id`, `action`, `resource_id` to `audit_logs` table.
