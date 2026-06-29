# Google Cloud Run Deployment - Step by Step Guide

Complete step-by-step instructions for deploying Travel Inbound to Google Cloud Run.

## Prerequisites Checklist

Before starting, ensure you have:
- [ ] Google Cloud account (sign up at https://cloud.google.com)
- [ ] Google Cloud SDK installed
- [ ] Docker Desktop installed (for local testing)
- [ ] Billing enabled on your GCP project

---

## Step 1: Install Google Cloud SDK

### Windows:
```powershell
# Download and install from:
# https://cloud.google.com/sdk/docs/install-windows

# Or use PowerShell:
(New-Object Net.WebClient).DownloadFile("https://dl.google.com/dl/cloudsdk/channels/rapid/GoogleCloudSDKInstaller.exe", "$env:Temp\GoogleCloudSDKInstaller.exe")
& $env:Temp\GoogleCloudSDKInstaller.exe
```

### macOS:
```bash
brew install google-cloud-sdk
```

### Linux:
```bash
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
```

**Verify installation:**
```bash
gcloud --version
```

---

## Step 2: Login and Set Up Project

### 2.1 Login to Google Cloud
```bash
gcloud auth login
```
This will open a browser window for authentication.

### 2.2 Create a New Project (or use existing)
```bash
# Create new project
gcloud projects create travel-inbound-project --name="Travel Inbound"

# Set as active project
gcloud config set project travel-inbound-project
```

**OR use existing project:**
```bash
# List projects
gcloud projects list

# Set active project
gcloud config set project YOUR_EXISTING_PROJECT_ID
```

### 2.3 Enable Billing
1. Go to: https://console.cloud.google.com/billing
2. Link a billing account to your project
3. Or enable free trial (if eligible)

---

## Step 3: Enable Required APIs

```bash
# Enable Cloud Run API
gcloud services enable run.googleapis.com

# Enable Container Registry API
gcloud services enable containerregistry.googleapis.com

# Enable Cloud Build API (optional, for CI/CD)
gcloud services enable cloudbuild.googleapis.com

# Enable Cloud SQL API (if using Cloud SQL)
gcloud services enable sqladmin.googleapis.com
```

**Verify APIs are enabled:**
```bash
gcloud services list --enabled
```

---

## Step 4: Set Up Cloud SQL Database (Recommended for Production)

### 4.1 Create Cloud SQL PostgreSQL Instance

```bash
gcloud sql instances create travel-inbound-db \
    --database-version=POSTGRES_15 \
    --tier=db-f1-micro \
    --region=us-central1 \
    --root-password=YOUR_SECURE_PASSWORD_HERE
```

**Important:** Replace `YOUR_SECURE_PASSWORD_HERE` with a strong password. Save it securely!

**Note:** `db-f1-micro` is the smallest/cheapest tier (~$7/month). For production, consider `db-f1-small` or higher.

### 4.2 Create Database

```bash
gcloud sql databases create travel_inbound --instance=travel-inbound-db
```

### 4.3 Create Database User

```bash
gcloud sql users create travel_user \
    --instance=travel-inbound-db \
    --password=YOUR_DB_USER_PASSWORD
```

**Save both passwords securely!**

### 4.4 Get Connection Name

```bash
gcloud sql instances describe travel-inbound-db --format="value(connectionName)"
```

**Save this connection name!** It looks like: `PROJECT_ID:REGION:INSTANCE_NAME`

---

## Step 5: Prepare Your Application

### 5.1 Verify Required Files Exist

Make sure these files are in your project root:
- ✅ `Dockerfile`
- ✅ `requirements.txt`
- ✅ `main.py`
- ✅ `app/` directory (your application code)

### 5.2 Test Docker Build Locally (Optional but Recommended)

```bash
# Build Docker image locally
docker build -t travel-inbound:test .

# Test run locally
docker run -p 8080:8080 -e PORT=8080 travel-inbound:test
```

Visit http://localhost:8080 to verify it works.

**Stop the container:**
```bash
docker stop $(docker ps -q --filter ancestor=travel-inbound:test)
```

---

## Step 6: Build and Push Docker Image

### 6.1 Set Your Project ID Variable

**Windows PowerShell:**
```powershell
$PROJECT_ID = gcloud config get-value project
```

**Linux/macOS:**
```bash
export PROJECT_ID=$(gcloud config get-value project)
echo $PROJECT_ID
```

### 6.2 Configure Docker for Google Container Registry

```bash
gcloud auth configure-docker
```

### 6.3 Build Docker Image

**Windows PowerShell:**
```powershell
docker build -t gcr.io/$PROJECT_ID/travel-inbound:latest .
```

**Linux/macOS:**
```bash
docker build -t gcr.io/${PROJECT_ID}/travel-inbound:latest .
```

This may take 5-10 minutes the first time.

### 6.4 Push Image to Container Registry

**Windows PowerShell:**
```powershell
docker push gcr.io/$PROJECT_ID/travel-inbound:latest
```

**Linux/macOS:**
```bash
docker push gcr.io/${PROJECT_ID}/travel-inbound:latest
```

This uploads your image to Google Container Registry.

---

## Step 7: Deploy to Cloud Run

### 7.1 Basic Deployment (Without Database)

**Windows PowerShell:**
```powershell
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

**Linux/macOS:**
```bash
gcloud run deploy travel-inbound \
    --image gcr.io/${PROJECT_ID}/travel-inbound:latest \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --timeout 300 \
    --max-instances 10 \
    --min-instances 0 \
    --set-env-vars "PORT=8080"
```

### 7.2 Deployment with Cloud SQL Connection

If you set up Cloud SQL in Step 4:

**Get your connection name first:**
```bash
CONNECTION_NAME=$(gcloud sql instances describe travel-inbound-db --format="value(connectionName)")
echo $CONNECTION_NAME
```

**Deploy with Cloud SQL:**

**Windows PowerShell:**
```powershell
$CONNECTION_NAME = gcloud sql instances describe travel-inbound-db --format="value(connectionName)"
$DB_PASSWORD = "YOUR_DB_USER_PASSWORD"  # Replace with actual password

gcloud run deploy travel-inbound `
    --image gcr.io/$PROJECT_ID/travel-inbound:latest `
    --platform managed `
    --region us-central1 `
    --add-cloudsql-instances $CONNECTION_NAME `
    --allow-unauthenticated `
    --memory 2Gi `
    --cpu 2 `
    --timeout 300 `
    --max-instances 10 `
    --min-instances 0 `
    --set-env-vars "PORT=8080,DATABASE_URL=postgresql://travel_user:$DB_PASSWORD@/travel_inbound?host=/cloudsql/$CONNECTION_NAME"
```

**Linux/macOS:**
```bash
CONNECTION_NAME=$(gcloud sql instances describe travel-inbound-db --format="value(connectionName)")
DB_PASSWORD="YOUR_DB_USER_PASSWORD"  # Replace with actual password

gcloud run deploy travel-inbound \
    --image gcr.io/${PROJECT_ID}/travel-inbound:latest \
    --platform managed \
    --region us-central1 \
    --add-cloudsql-instances ${CONNECTION_NAME} \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --timeout 300 \
    --max-instances 10 \
    --min-instances 0 \
    --set-env-vars "PORT=8080,DATABASE_URL=postgresql://travel_user:${DB_PASSWORD}@/travel_inbound?host=/cloudsql/${CONNECTION_NAME}"
```

---

## Step 8: Configure Environment Variables

### 8.1 Set Session Secret

**Generate a random secret:**
```bash
# Linux/macOS
openssl rand -hex 32

# Windows PowerShell
-join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | ForEach-Object {[char]$_})
```

### 8.2 Update Environment Variables

```bash
gcloud run services update travel-inbound \
    --region us-central1 \
    --update-env-vars "SESSION_SECRET=YOUR_GENERATED_SECRET,SESSION_COOKIE_SECURE=true"
```

**Replace `YOUR_GENERATED_SECRET` with the secret from Step 8.1**

---

## Step 9: Get Your Service URL

```bash
gcloud run services describe travel-inbound --region us-central1 --format 'value(status.url)'
```

**Or view in Cloud Console:**
1. Go to: https://console.cloud.google.com/run
2. Click on your service name
3. Copy the URL from the top

---

## Step 10: Initialize Database (If Using Cloud SQL)

### 10.1 Connect to Cloud SQL

You need to initialize your database tables. Options:

**Option A: Use Cloud SQL Proxy (Recommended)**

1. Download Cloud SQL Proxy:
   - Windows: https://dl.google.com/cloudsql/cloud_sql_proxy_x64.exe
   - Linux/macOS: https://dl.google.com/cloudsql/cloud_sql_proxy.linux.amd64

2. Start proxy:
```bash
# Windows
.\cloud_sql_proxy_x64.exe -instances=CONNECTION_NAME=tcp:5432

# Linux/macOS
./cloud_sql_proxy -instances=CONNECTION_NAME=tcp:5432
```

3. In another terminal, run your init script:
```bash
export DATABASE_URL="postgresql://travel_user:YOUR_PASSWORD@localhost:5432/travel_inbound"
python init_db.py
```

**Option B: Use Cloud Shell**

1. Go to: https://shell.cloud.google.com
2. Upload your `init_db.py` file
3. Install dependencies and run:
```bash
pip install -r requirements.txt
export DATABASE_URL="postgresql://travel_user:PASSWORD@/travel_inbound?host=/cloudsql/CONNECTION_NAME"
python init_db.py
```

---

## Step 11: Test Your Deployment

### 11.1 Visit Your Service URL

Open the URL from Step 9 in your browser.

### 11.2 Check Logs

```bash
# View recent logs
gcloud run services logs read travel-inbound --region us-central1

# Follow logs in real-time
gcloud run services logs tail travel-inbound --region us-central1
```

### 11.3 Check Service Status

```bash
gcloud run services describe travel-inbound --region us-central1
```

---

## Step 12: Update Deployment (When You Make Changes)

### 12.1 Rebuild and Push New Image

```bash
# Set project ID
export PROJECT_ID=$(gcloud config get-value project)  # Linux/macOS
# OR
$PROJECT_ID = gcloud config get-value project  # PowerShell

# Rebuild
docker build -t gcr.io/${PROJECT_ID}/travel-inbound:latest .

# Push
docker push gcr.io/${PROJECT_ID}/travel-inbound:latest

# Redeploy (uses latest image)
gcloud run deploy travel-inbound \
    --image gcr.io/${PROJECT_ID}/travel-inbound:latest \
    --region us-central1
```

---

## Troubleshooting

### Issue: "Permission denied" errors

**Solution:**
```bash
# Ensure you're authenticated
gcloud auth login

# Verify project is set
gcloud config get-value project
```

### Issue: Docker build fails

**Solution:**
- Check `Dockerfile` syntax
- Verify `requirements.txt` exists
- Check internet connection for package downloads

### Issue: Service won't start

**Solution:**
```bash
# Check logs
gcloud run services logs read travel-inbound --region us-central1 --limit 50

# Check environment variables
gcloud run services describe travel-inbound --region us-central1
```

### Issue: Database connection fails

**Solution:**
- Verify Cloud SQL instance is running
- Check connection name format
- Verify DATABASE_URL environment variable
- Ensure Cloud SQL connection is added: `--add-cloudsql-instances`

### Issue: "Image not found"

**Solution:**
- Verify image was pushed successfully
- Check image name matches exactly
- Ensure you're using correct project ID

---

## Quick Reference Commands

```bash
# Get project ID
gcloud config get-value project

# List services
gcloud run services list --region us-central1

# View service details
gcloud run services describe travel-inbound --region us-central1

# View logs
gcloud run services logs read travel-inbound --region us-central1

# Update environment variables
gcloud run services update travel-inbound --region us-central1 --update-env-vars "KEY=VALUE"

# Delete service
gcloud run services delete travel-inbound --region us-central1
```

---

## Cost Estimation

- **Cloud Run**: ~$0.40 per million requests (first 2 million free)
- **Cloud SQL (db-f1-micro)**: ~$7-10/month
- **Container Registry**: ~$0.026/GB/month (first 5GB free)
- **Total**: ~$10-15/month for low traffic

---

## Next Steps

1. ✅ Set up custom domain
2. ✅ Configure SSL certificate
3. ✅ Set up monitoring and alerts
4. ✅ Configure automated backups
5. ✅ Set up CI/CD pipeline

---

## Summary Checklist

- [ ] Google Cloud SDK installed
- [ ] Logged in: `gcloud auth login`
- [ ] Project created and set: `gcloud config set project`
- [ ] APIs enabled
- [ ] Cloud SQL instance created (optional)
- [ ] Docker image built: `docker build`
- [ ] Docker image pushed: `docker push`
- [ ] Deployed to Cloud Run: `gcloud run deploy`
- [ ] Environment variables configured
- [ ] Database initialized (if using Cloud SQL)
- [ ] Service URL obtained
- [ ] Application tested and working

**Your application is now live on Google Cloud Run! 🎉**
