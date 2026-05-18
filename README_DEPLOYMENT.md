# Quick Start: Deploy to Google Cloud Run

## Prerequisites

1. Install [Google Cloud SDK](https://cloud.google.com/sdk/docs/install)
2. Install [Docker Desktop](https://www.docker.com/products/docker-desktop)
3. Authenticate: `gcloud auth login`
4. Set project: `gcloud config set project YOUR_PROJECT_ID`

## Quick Deployment (Windows PowerShell)

```powershell
.\deploy.ps1
```

## Quick Deployment (Linux/macOS)

```bash
chmod +x deploy.sh
./deploy.sh
```

## Manual Deployment

### 1. Build and Push Docker Image

```bash
export PROJECT_ID=your-project-id
docker build -t gcr.io/$PROJECT_ID/travel-inbound:latest .
docker push gcr.io/$PROJECT_ID/travel-inbound:latest
```

### 2. Deploy to Cloud Run

```bash
gcloud run deploy travel-inbound \
    --image gcr.io/$PROJECT_ID/travel-inbound:latest \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --timeout 300
```

## Database Setup

### For Production: Use Cloud SQL (PostgreSQL)

1. Create Cloud SQL instance:
```bash
gcloud sql instances create travel-inbound-db \
    --database-version=POSTGRES_15 \
    --tier=db-f1-micro \
    --region=us-central1
```

2. Create database:
```bash
gcloud sql databases create travel_inbound --instance=travel-inbound-db
```

3. Get connection name:
```bash
gcloud sql instances describe travel-inbound-db --format="value(connectionName)"
```

4. Deploy with Cloud SQL connection:
```bash
gcloud run deploy travel-inbound \
    --image gcr.io/$PROJECT_ID/travel-inbound:latest \
    --add-cloudsql-instances PROJECT_ID:REGION:INSTANCE_NAME \
    --set-env-vars "DATABASE_URL=postgresql://user:password@/travel_inbound?host=/cloudsql/PROJECT_ID:REGION:INSTANCE_NAME"
```

## Environment Variables

Set these in Cloud Run console or via CLI:

- `DATABASE_URL`: PostgreSQL connection string (for Cloud SQL)
- `SESSION_SECRET`: Random secret key for sessions
- `SESSION_COOKIE_SECURE`: Set to `true` in production
- `OPENAI_API_KEY`: (Optional) If using AI features
- `PORT`: Automatically set by Cloud Run (8080)

## Files Created

- `Dockerfile`: Container configuration
- `.dockerignore`: Files to exclude from build
- `requirements.txt`: Python dependencies
- `cloudbuild.yaml`: Automated CI/CD configuration
- `deploy.sh` / `deploy.ps1`: Quick deployment scripts
- `DEPLOYMENT.md`: Detailed deployment guide

## Next Steps

1. **Set up Cloud SQL** for persistent database storage
2. **Configure environment variables** in Cloud Run
3. **Set up custom domain** (optional)
4. **Enable monitoring** and alerts
5. **Configure secrets** using Secret Manager

For detailed instructions, see [DEPLOYMENT.md](DEPLOYMENT.md)
