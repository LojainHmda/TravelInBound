# Deploy with Persistent Database

**Problem:** Without `DATABASE_URL`, Cloud Run uses SQLite with an ephemeral filesystem. Data is lost on every cold start or redeploy.

**Solution:** Pass your database URL when deploying.

## Option 1: Hosted PostgreSQL (Supabase, Neon, Railway, etc.)

```powershell
gcloud builds submit --config cloudbuild.yaml . `
  --substitutions="_DATABASE_URL=postgresql://user:password@host:5432/database"
```

## Option 2: Google Cloud SQL

1. Get your Cloud SQL connection name:
   ```powershell
   gcloud sql instances describe YOUR_INSTANCE --format="value(connectionName)"
   ```
   Example output: `kartacagenai:us-central1:travel-inbound-db`

2. Deploy with both substitutions:
   ```powershell
   gcloud builds submit --config cloudbuild.yaml . `
     --substitutions="_DATABASE_URL=postgresql://user:password@/database?host=/cloudsql/kartacagenai:us-central1:travel-inbound-db,_CLOUD_SQL_INSTANCE=kartacagenai:us-central1:travel-inbound-db"
   ```

## Option 3: Set Once in Cloud Run Console (Not Recommended)

You can set `DATABASE_URL` in Cloud Run Console → travel-inbound → Edit & Deploy → Variables.  
**Warning:** Each `gcloud builds submit` will overwrite env vars with only what's in cloudbuild.yaml. To persist DATABASE_URL across deploys, you must pass it via `--substitutions` (Options 1 or 2 above).

## Quick Fix: Add DATABASE_URL to Existing Deployment

If you already have a deployed service and just need to add the database without a full rebuild:

```powershell
gcloud run services update travel-inbound --region us-central1 --update-env-vars "DATABASE_URL=postgresql://user:password@host:5432/database"
```

For Cloud SQL, also add the instance:
```powershell
gcloud run services update travel-inbound --region us-central1 --add-cloudsql-instances "PROJECT:REGION:INSTANCE" --update-env-vars "DATABASE_URL=postgresql://user:password@/database?host=/cloudsql/PROJECT:REGION:INSTANCE"
```

## Verify

After deploy, check that the env var is set:
```powershell
gcloud run services describe travel-inbound --region us-central1 --format="yaml(spec.template.spec.containers[0].env)"
```
