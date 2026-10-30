# Database Connection Timeout Troubleshooting Guide

## Symptom
Application logs report `OperationalError: could not connect to server: Connection timed out` or `FATAL: remaining connection slots are reserved for non-replication superuser connections`.

## Step-by-Step Resolution
1. **Check Active Connections:**
   ```sql
   SELECT count(*), state FROM pg_stat_activity GROUP BY state;
   ```
2. **Identify Idle In Transaction Queries:**
   ```sql
   SELECT pid, now() - query_start AS duration, query
   FROM pg_stat_activity
   WHERE state = 'idle in transaction' AND (now() - query_start) > interval '2 minutes';
   ```
3. **Verify PgBouncer / Connection Pool:**
   - Verify connection pool size in `DATABASE_URL` (`pool_size=20`, `max_overflow=10`).
   - Ensure clients gracefully release connections back to the pool in exception handlers.
4. **Tune Keepalives & Timeout Thresholds:**
   - Set `tcp_keepalives_idle = 60`
   - Set `statement_timeout = 30000` (30 seconds)
