# Next Steps: Deploy to Google Cloud Run

Follow these steps in order to deploy your application:

## Step 1: Install Prerequisites ✅

### Install Google Cloud SDK
- **Windows**: Download from https://cloud.google.com/sdk/docs/install-windows
- **macOS**: `brew install google-cloud-sdk`
- **Linux**: Follow https://cloud.google.com/sdk/docs/install

### Install Docker Desktop
- Download from https://www.docker.com/products/docker-desktop
- Make sure Docker is running before proceeding

## Step 2: Set Up Google Cloud Project 🔧

```powershell
# Login to Google Cloud
gcloud auth login

# Create a new project (or use existing)
gcloud projects create travel-inbound-project --name="Travel Inbound"

# Set as active project
gcloud config set project travel-inbound-project

# Enable required APIs
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable sqladmin.googleapis.com
```

## Step 3: Test Docker Build Locally (Recommended) 🐳

```powershell
# Build the Docker image locally to test
docker build -t travel-inbound:test .

# Test run locally (optional)
docker run -p 8080:8080 -e PORT=8080 travel-inbound:test
```

If this works, you can access http://localhost:8080 to verify.

## Step 4: Set Up Cloud SQL Database (Production) 🗄️

**Important**: Cloud Run containers are stateless. For production, you need Cloud SQL.

```powershell
# Create Cloud SQL PostgreSQL instance
gcloud sql instances create travel-inbound-db `
    --database-version=POSTGRES_15 `
    --tier=db-f1-micro `
    --region=us-central1 `
    --root-password=YOUR_SECURE_PASSWORD_HERE

# Create the database
gcloud sql databases create travel_inbound --instance=travel-inbound-db

# Get connection name (save this!)
gcloud sql instances describe travel-inbound-db --format="value(connectionName)"
```

**Note**: Replace `YOUR_SECURE_PASSWORD_HERE` with a strong password. Save it securely!

## Step 5: Deploy to Cloud Run 🚀

### Option A: Quick Deploy (Using Script)

**Windows:**
```powershell
.\deploy.ps1
```

**Linux/macOS:**
```bash
chmod +x deploy.sh
./deploy.sh
```

### Option B: Manual Deploy

```powershell
# Set your project ID
$PROJECT_ID = gcloud config get-value project

# Build and push image
docker build -t gcr.io/$PROJECT_ID/travel-inbound:latest .
docker push gcr.io/$PROJECT_ID/travel-inbound:latest

# Deploy to Cloud Run
gcloud run deploy travel-inbound `
    --image gcr.io/$PROJECT_ID/travel-inbound:latest `
    --platform managed `
    --region us-central1 `
    --allow-unauthenticated `
    --memory 2Gi `
    --cpu 2 `
    --timeout 300 `
    --max-instances 10 `
    --min-instances 0 `
    --set-env-vars "PORT=8080"
```

## Step 6: Configure Database Connection 🔗

After deployment, you need to connect Cloud Run to Cloud SQL:

```powershell
# Get your connection name from Step 4
$CONNECTION_NAME = "PROJECT_ID:REGION:INSTANCE_NAME"

# Update Cloud Run service with Cloud SQL connection
gcloud run services update travel-inbound `
    --region us-central1 `
    --add-cloudsql-instances $CONNECTION_NAME `
    --update-env-vars "DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@/travel_inbound?host=/cloudsql/$CONNECTION_NAME"
```

**Important**: 
- Replace `YOUR_PASSWORD` with the password you set in Step 4
- Replace `CONNECTION_NAME` with the actual connection name from Step 4
- The format is: `PROJECT_ID:REGION:INSTANCE_NAME`

## Step 7: Set Environment Variables 🔐

```powershell
# Set session secret (generate a random one)
$SESSION_SECRET = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | ForEach-Object {[char]$_})

# Update environment variables
gcloud run services update travel-inbound `
    --region us-central1 `
    --update-env-vars "SESSION_SECRET=$SESSION_SECRET,SESSION_COOKIE_SECURE=true"
```

## Step 8: Initialize Database Tables 📊

After connecting to Cloud SQL, initialize your database:

```powershell
# Option 1: Use Cloud SQL Proxy (recommended)
# Download Cloud SQL Proxy: https://cloud.google.com/sql/docs/postgres/sql-proxy
# Then run your init script locally through the proxy

# Option 2: Create a Cloud Run Job (advanced)
# Or manually run SQL commands through Cloud Console
```

You can run your `init_db.py` script through Cloud SQL Proxy or create a one-time Cloud Run job.

## Step 9: Get Your Service URL 🌐

```powershell
# Get the service URL
gcloud run services describe travel-inbound --region us-central1 --format 'value(status.url)'
```

Visit this URL in your browser to test the application!

## Step 10: Verify Deployment ✅

1. **Check logs**:
   ```powershell
   gcloud run services logs read travel-inbound --region us-central1
   ```

2. **Test the application**:
   - Visit your service URL
   - Check if pages load correctly
   - Test database connectivity

3. **Monitor in Cloud Console**:
   - Go to https://console.cloud.google.com/run
   - Click on your service
   - Check metrics and logs

## Troubleshooting 🔧

### If deployment fails:
- Check Docker build logs: `docker build -t test .`
- Verify all dependencies in `requirements.txt`
- Check Cloud Run logs: `gcloud run services logs read travel-inbound --region us-central1`

### If database connection fails:
- Verify Cloud SQL instance is running
- Check connection name format
- Ensure Cloud Run service has Cloud SQL connection permission
- Verify database credentials

### If app doesn't start:
- Check logs for errors
- Verify PORT environment variable (should be 8080)
- Check memory limits (increase if needed)

## Cost Estimation 💰

- **Cloud Run**: Pay per request (~$0.40 per million requests)
- **Cloud SQL (db-f1-micro)**: ~$7-10/month
- **Container Registry**: ~$0.026/GB/month
- **Total**: ~$10-15/month for low traffic

## Next Steps After Deployment 🎯

1. **Set up custom domain** (optional)
2. **Configure monitoring and alerts**
3. **Set up CI/CD** with Cloud Build triggers
4. **Backup strategy** for Cloud SQL
5. **Performance optimization** based on usage

## Need Help? 📚

- Full documentation: See `DEPLOYMENT.md`
- Google Cloud Run docs: https://cloud.google.com/run/docs
- Cloud SQL docs: https://cloud.google.com/sql/docs

---

**Ready to start? Begin with Step 1!** 🚀
