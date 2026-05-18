# Google Cloud Run Deployment Guide

This guide will help you deploy the Travel Inbound application to Google Cloud Run.

## Prerequisites

1. **Google Cloud Account**: Sign up at [cloud.google.com](https://cloud.google.com)
2. **Google Cloud SDK**: Install the [gcloud CLI](https://cloud.google.com/sdk/docs/install)
3. **Docker**: Install [Docker Desktop](https://www.docker.com/products/docker-desktop) (for local testing)
4. **Project Setup**: Create a new GCP project or use an existing one

## Initial Setup

### 1. Install Google Cloud SDK

```bash
# Windows (PowerShell)
(New-Object Net.WebClient).DownloadFile("https://dl.google.com/dl/cloudsdk/channels/rapid/GoogleCloudSDKInstaller.exe", "$env:Temp\GoogleCloudSDKInstaller.exe")
& $env:Temp\GoogleCloudSDKInstaller.exe

# macOS
brew install google-cloud-sdk

# Linux
curl https://sdk.cloud.google.com | bash
```

### 2. Authenticate and Set Project

```bash
# Login to Google Cloud
gcloud auth login

# Set your project ID (replace YOUR_PROJECT_ID)
gcloud config set project YOUR_PROJECT_ID

# Enable required APIs
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable sqladmin.googleapis.com  # If using Cloud SQL
```

## Database Setup

### Option 1: Cloud SQL (PostgreSQL) - Recommended for Production

1. **Create Cloud SQL Instance**:

```bash
gcloud sql instances create travel-inbound-db \
    --database-version=POSTGRES_15 \
    --tier=db-f1-micro \
    --region=us-central1 \
    --root-password=YOUR_SECURE_PASSWORD
```

2. **Create Database**:

```bash
gcloud sql databases create travel_inbound --instance=travel-inbound-db
```

3. **Get Connection Name**:

```bash
gcloud sql instances describe travel-inbound-db --format="value(connectionName)"
```

4. **Set Environment Variable**:

The connection string format:
```
postgresql://USERNAME:PASSWORD@/DATABASE_NAME?host=/cloudsql/CONNECTION_NAME
```

### Option 2: SQLite (Development/Testing)

SQLite will work on Cloud Run but data will be ephemeral (lost on container restart). For production, use Cloud SQL.

## Environment Variables

Create a `.env.yaml` file or set environment variables in Cloud Run:

```yaml
DATABASE_URL: "postgresql://user:password@/travel_inbound?host=/cloudsql/PROJECT_ID:REGION:INSTANCE_NAME"
SESSION_SECRET: "your-secret-key-here-change-in-production"
SESSION_COOKIE_SECURE: "true"
OPENAI_API_KEY: "your-openai-api-key-if-needed"
```

## Deployment Methods

### Method 1: Using Cloud Build (Automated CI/CD)

1. **Push code to a Git repository** (GitHub, GitLab, etc.)

2. **Connect repository to Cloud Build**:
   - Go to Cloud Console → Cloud Build → Triggers
   - Create a new trigger
   - Connect your repository
   - Set build configuration to use `cloudbuild.yaml`

3. **Deploy manually**:

```bash
gcloud builds submit --config cloudbuild.yaml
```

### Method 2: Manual Deployment with gcloud

1. **Build and push the container**:

```bash
# Set your project ID
export PROJECT_ID=your-project-id

# Build the image
docker build -t gcr.io/$PROJECT_ID/travel-inbound:latest .

# Push to Container Registry
docker push gcr.io/$PROJECT_ID/travel-inbound:latest
```

2. **Deploy to Cloud Run**:

```bash
gcloud run deploy travel-inbound \
    --image gcr.io/$PROJECT_ID/travel-inbound:latest \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --timeout 300 \
    --max-instances 10 \
    --min-instances 0 \
    --set-env-vars "PORT=8080,DATABASE_URL=your-database-url,SESSION_SECRET=your-secret"
```

### Method 3: Using Cloud Run with Cloud SQL

If using Cloud SQL, add the Cloud SQL connection:

```bash
gcloud run deploy travel-inbound \
    --image gcr.io/$PROJECT_ID/travel-inbound:latest \
    --platform managed \
    --region us-central1 \
    --add-cloudsql-instances PROJECT_ID:REGION:INSTANCE_NAME \
    --set-env-vars "DATABASE_URL=postgresql://user:password@/travel_inbound?host=/cloudsql/PROJECT_ID:REGION:INSTANCE_NAME"
```

## Post-Deployment

### 1. Initialize Database

After deployment, you may need to initialize the database:

```bash
# Get the Cloud Run service URL
SERVICE_URL=$(gcloud run services describe travel-inbound --region us-central1 --format 'value(status.url)')

# Run database initialization (if you have a script)
# You may need to create a Cloud Run job or run locally with Cloud SQL proxy
```

### 2. Set Up Custom Domain (Optional)

```bash
gcloud run domain-mappings create \
    --service travel-inbound \
    --domain your-domain.com \
    --region us-central1
```

### 3. Configure HTTPS

Cloud Run automatically provides HTTPS. Ensure `SESSION_COOKIE_SECURE` is set to `true` in production.

## Monitoring and Logs

### View Logs

```bash
gcloud run services logs read travel-inbound --region us-central1
```

### View Metrics

- Go to Cloud Console → Cloud Run → travel-inbound → Metrics

## Troubleshooting

### Common Issues

1. **Database Connection Errors**:
   - Verify Cloud SQL instance is running
   - Check connection name format
   - Ensure Cloud Run service has Cloud SQL connection permission

2. **Port Issues**:
   - Cloud Run uses the `PORT` environment variable (default: 8080)
   - Ensure your app listens on `0.0.0.0:$PORT`

3. **Memory Issues**:
   - Increase memory allocation: `--memory 4Gi`
   - Check application logs for memory errors

4. **Timeout Issues**:
   - Increase timeout: `--timeout 300` (max 3600 seconds)
   - Optimize long-running operations

### Health Checks

Add a health check endpoint to your Flask app:

```python
@app.route('/health')
def health():
    return {'status': 'healthy'}, 200
```

## Cost Optimization

1. **Set min-instances to 0** for cost savings (cold starts may occur)
2. **Use Cloud SQL Proxy** for database connections
3. **Enable request concurrency** (default: 80)
4. **Monitor usage** in Cloud Console

## Security Best Practices

1. **Never commit secrets** to version control
2. **Use Secret Manager** for sensitive data:
   ```bash
   echo -n "your-secret" | gcloud secrets create session-secret --data-file=-
   ```
3. **Enable IAM** authentication for Cloud Run (remove `--allow-unauthenticated`)
4. **Use Cloud SQL** with private IP for database
5. **Enable VPC** connector if needed

## Scaling

Cloud Run automatically scales based on traffic:
- **Min instances**: 0 (saves cost, may have cold starts)
- **Max instances**: 10 (adjust based on needs)
- **Concurrency**: 80 requests per instance (default)

## Rollback

If you need to rollback:

```bash
# List revisions
gcloud run revisions list --service travel-inbound --region us-central1

# Rollback to previous revision
gcloud run services update-traffic travel-inbound \
    --to-revisions REVISION_NAME=100 \
    --region us-central1
```

## Support

For issues or questions:
- Check Cloud Run [documentation](https://cloud.google.com/run/docs)
- Review application logs in Cloud Console
- Check Cloud SQL connection logs if using Cloud SQL
