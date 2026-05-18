# Deploy Now – Quick Reference

## 1. Set DATABASE_URL in `.env`

Create or edit `.env` in the project root:

**Option A – Hosted PostgreSQL (Supabase, Neon, Railway):**
```env
DATABASE_URL=postgresql://user:password@host:5432/database?sslmode=require
```

**Option B – Google Cloud SQL:**
```env
DATABASE_URL=postgresql://user:password@/database?host=/cloudsql/PROJECT_ID:us-central1:INSTANCE_NAME
CLOUD_SQL_INSTANCE=PROJECT_ID:us-central1:INSTANCE_NAME
```

Replace `user`, `password`, `host`, `database`, and `PROJECT_ID:INSTANCE_NAME` with your values.

---

## 2. Deploy

```powershell
.\deploy.ps1
```

Or with explicit database URL:
```powershell
.\deploy.ps1 -DatabaseUrl "postgresql://user:password@host:5432/database?sslmode=require"
```

---

## 3. Get Your Deployment URL

After deploy, run:
```powershell
gcloud run services describe travel-inbound --region us-central1 --format 'value(status.url)'
```

Or verify and get URL:
```powershell
.\verify-production.ps1
```

---

## 4. Quick Fix – Add DATABASE_URL to Existing Deployment

If the app is already deployed but data is not persisting:

```powershell
# 1. Add to .env first, then:
.\fix-production-database.ps1
```

---

## Your Deployment URL Format

- **Cloud Run:** `https://travel-inbound-XXXXX-uc.a.run.app`
- **Health check:** `https://YOUR-URL/health`
