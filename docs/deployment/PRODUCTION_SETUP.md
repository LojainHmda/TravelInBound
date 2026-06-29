# Production Setup – Data Persistence

**Problem:** Production data disappears because Cloud Run uses ephemeral storage. Without PostgreSQL, data is lost on every container restart.

**Solution:** Use PostgreSQL and set `DATABASE_URL` before every deploy.

---

## Pre-Deploy Checklist (Production = Local)

1. **`.env`** – Contains `DATABASE_URL=postgresql://...` (Neon/Cloud SQL)
2. **Schema** – Run `python run_production_migrations.py` once to add missing columns to existing DB
3. **CSRF** – All `/inbound/api/*`, `/booking/api/*`, `/customers/api/*` are exempt (no 400 errors)
4. **Health** – After deploy, `/health` shows `db_connected`, `schema_ok`, `database_url_set`

---

## Quick Setup (First Time)

### 1. Create a PostgreSQL database

Choose one:

- **Supabase** (free tier): [supabase.com](https://supabase.com) → New Project → Settings → Database → Connection string
- **Neon** (free tier): [neon.tech](https://neon.tech) → Create project → Connection string
- **Railway**: [railway.app](https://railway.app) → New Project → PostgreSQL
- **Google Cloud SQL**: See [DEPLOY_WITH_DATABASE.md](DEPLOY_WITH_DATABASE.md)

### 2. Create `.env` in project root

```env
DATABASE_URL=postgresql://user:password@host:5432/database?sslmode=require
```

For Cloud SQL (unix socket):

```env
DATABASE_URL=postgresql://user:password@/database?host=/cloudsql/PROJECT:REGION:INSTANCE
CLOUD_SQL_INSTANCE=PROJECT:REGION:INSTANCE
```

### 3. Deploy

```powershell
.\deploy-cloud-run.ps1
```

Or with Cloud Build (no local Docker):

```powershell
.\deploy-cloudbuild.ps1
```

The script will load `.env`, require `DATABASE_URL`, and run a health check after deploy.

---

## Fix Existing Deployment (Data Not Persisting)

If production was deployed without `DATABASE_URL`:

1. Create `.env` with your PostgreSQL URL (see above).
2. Run:

```powershell
.\fix-production-database.ps1
```

This updates the Cloud Run service with `DATABASE_URL` without a full rebuild.

---

## Verify Production

```powershell
.\verify-production.ps1
```

Or open: `https://your-service.run.app/health`

You should see:

- `database_url_set: true`
- `db_connected: true`
- `schema_ok: true`

---

## Run Schema Migrations Manually

If the health check reports missing columns:

```powershell
$env:DATABASE_URL = "postgresql://user:pass@host:5432/db"
python run_production_migrations.py
```

---

## Summary

| Step | Action |
|------|--------|
| 1 | Create PostgreSQL (Supabase/Neon/Railway/Cloud SQL) |
| 2 | Add `DATABASE_URL` to `.env` |
| 3 | Deploy with `.\deploy-cloud-run.ps1` or `.\deploy-cloudbuild.ps1` |
| 4 | Run `.\verify-production.ps1` to confirm |
