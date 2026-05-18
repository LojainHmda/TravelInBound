# Deploy Travel Inbound via Google Cloud Console

Your gcloud has permission issues with the Cloud Build bucket. Use the Console instead:

## Option 1: Fix permissions then re-run script (recommended)

1. Open **Cloud Console** → **IAM & Admin** → **IAM**:  
   https://console.cloud.google.com/iam-admin/iam?project=kartacagenai

2. Find **lojainhmda@gmail.com** and ensure they have **Owner** or these roles:
   - **Storage Admin** (storage.admin)
   - **Service Usage Consumer** (serviceusage.services.use)
   - **Cloud Build Editor** (cloudbuild.builds.create)

3. Open **Storage** → **Buckets**:  
   https://console.cloud.google.com/storage/browser?project=kartacagenai

4. Open bucket **kartacagenai_cloudbuild** → **Permissions** → **Grant Access**  
   - Principal: `lojainhmda@gmail.com`  
   - Role: **Storage Admin**  
   - Save

5. Re-run the deploy script:
   ```powershell
   .\install-and-deploy.ps1
   ```

---

## Option 2: Deploy from Cloud Build Console

1. Go to **Cloud Build** → **History**:  
   https://console.cloud.google.com/cloud-build/builds?project=kartacagenai

2. Click **Submit build**.

3. Set:
   - **Region**: us-central1
   - **Source**: **Upload** (zip your project folder and upload)
   - **Build configuration**: **Cloud Build configuration file**
   - **Cloud Build configuration file location**: `cloudbuild.yaml` (leave default if uploading from repo root)

4. Click **Submit**.

---

## Option 3: Build with Docker locally (if Docker is installed)

```powershell
# Build and push
docker build -t gcr.io/kartacagenai/travel-inbound:latest .
docker push gcr.io/kartacagenai/travel-inbound:latest

# Deploy
gcloud run deploy travel-inbound --image gcr.io/kartacagenai/travel-inbound:latest --region us-central1 --allow-unauthenticated --platform managed
```
