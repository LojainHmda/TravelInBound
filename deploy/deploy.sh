#!/bin/bash
# Google Cloud Run Deployment Script
# This script handles the complete deployment process

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Default values
PROJECT_ID=""
REGION="us-central1"
SERVICE_NAME="travel-inbound"
SKIP_BUILD=false
SKIP_PUSH=false
DATABASE_URL=""
SESSION_SECRET=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --project-id)
            PROJECT_ID="$2"
            shift 2
            ;;
        --region)
            REGION="$2"
            shift 2
            ;;
        --service-name)
            SERVICE_NAME="$2"
            shift 2
            ;;
        --skip-build)
            SKIP_BUILD=true
            shift
            ;;
        --skip-push)
            SKIP_PUSH=true
            shift
            ;;
        --database-url)
            DATABASE_URL="$2"
            shift 2
            ;;
        --session-secret)
            SESSION_SECRET="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--project-id PROJECT] [--region REGION] [--service-name NAME] [--database-url URL] [--session-secret SECRET] [--skip-build] [--skip-push]"
            exit 1
            ;;
    esac
done

echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}  Travel Inbound - Cloud Run Deployment${NC}"
echo -e "${CYAN}========================================${NC}\n"

# Step 1: Get or set project ID
if [ -z "$PROJECT_ID" ]; then
    PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
    if [ -z "$PROJECT_ID" ]; then
        echo -e "${RED}✗ No GCP project set.${NC}"
        echo -e "${YELLOW}  Set it with: gcloud config set project YOUR_PROJECT_ID${NC}"
        echo -e "${YELLOW}  OR use: $0 --project-id YOUR_PROJECT_ID${NC}"
        exit 1
    fi
fi

echo -e "${CYAN}>>> Using Project: ${PROJECT_ID}${NC}"
echo -e "${CYAN}>>> Region: ${REGION}${NC}"
echo -e "${CYAN}>>> Service: ${SERVICE_NAME}${NC}\n"

# Step 2: Verify prerequisites
echo -e "${CYAN}>>> Checking prerequisites...${NC}"

# Check Docker
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version)
    echo -e "${GREEN}✓ Docker found: ${DOCKER_VERSION}${NC}"
else
    echo -e "${RED}✗ Docker not found. Please install Docker.${NC}"
    exit 1
fi

# Check gcloud
if command -v gcloud &> /dev/null; then
    echo -e "${GREEN}✓ gcloud CLI found${NC}"
else
    echo -e "${RED}✗ gcloud CLI not found. Please install Google Cloud SDK.${NC}"
    exit 1
fi

# Check if logged in
CURRENT_ACCOUNT=$(gcloud config get-value account 2>/dev/null)
if [ -z "$CURRENT_ACCOUNT" ]; then
    echo -e "${YELLOW}⚠ Not logged in to gcloud. Attempting login...${NC}"
    gcloud auth login
    if [ $? -ne 0 ]; then
        echo -e "${RED}✗ Failed to login. Please run: gcloud auth login${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}✓ Logged in as: ${CURRENT_ACCOUNT}${NC}\n"

# Step 3: Enable required APIs
echo -e "${CYAN}>>> Enabling required Google Cloud APIs...${NC}"
APIS=(
    "cloudbuild.googleapis.com"
    "run.googleapis.com"
    "containerregistry.googleapis.com"
    "sqladmin.googleapis.com"
)

for api in "${APIS[@]}"; do
    echo -n "  Checking $api... "
    if gcloud services list --enabled --filter="name:$api" --format="value(name)" 2>/dev/null | grep -q "$api"; then
        echo -e "${GREEN}Already enabled${NC}"
    else
        gcloud services enable "$api" --quiet 2>/dev/null
        echo -e "${GREEN}Enabled${NC}"
    fi
done

# Step 4: Build Docker image
if [ "$SKIP_BUILD" = false ]; then
    echo -e "\n${CYAN}>>> Building Docker image...${NC}"
    IMAGE_TAG="gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest"
    
    docker build -t "$IMAGE_TAG" .
    if [ $? -ne 0 ]; then
        echo -e "${RED}✗ Docker build failed!${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Docker image built successfully: ${IMAGE_TAG}${NC}"
else
    echo -e "\n${YELLOW}⚠ Skipping Docker build (--skip-build flag)${NC}"
fi

# Step 5: Push to Container Registry
if [ "$SKIP_PUSH" = false ]; then
    echo -e "\n${CYAN}>>> Pushing image to Container Registry...${NC}"
    IMAGE_TAG="gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest"
    
    docker push "$IMAGE_TAG"
    if [ $? -ne 0 ]; then
        echo -e "${RED}✗ Docker push failed!${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Image pushed successfully${NC}"
else
    echo -e "\n${YELLOW}⚠ Skipping Docker push (--skip-push flag)${NC}"
fi

# Step 6: Prepare environment variables
echo -e "\n${CYAN}>>> Preparing environment variables...${NC}"

ENV_VARS=("PORT=8080")

# Generate session secret if not provided
if [ -z "$SESSION_SECRET" ]; then
    SESSION_SECRET=$(openssl rand -hex 16)
    echo -e "${YELLOW}⚠ Generated new SESSION_SECRET (save this for future deployments!)${NC}"
    echo -e "${YELLOW}  SESSION_SECRET: ${SESSION_SECRET}${NC}"
fi

ENV_VARS+=("SESSION_SECRET=${SESSION_SECRET}")
ENV_VARS+=("SESSION_COOKIE_SECURE=true")

# Add database URL if provided
if [ -n "$DATABASE_URL" ]; then
    ENV_VARS+=("DATABASE_URL=${DATABASE_URL}")
    echo -e "${GREEN}✓ Database URL configured${NC}"
else
    echo -e "${YELLOW}⚠ No DATABASE_URL provided. Using default SQLite (ephemeral).${NC}"
    echo -e "${YELLOW}  For production, use Cloud SQL and provide DATABASE_URL${NC}"
fi

ENV_VARS_STRING=$(IFS=,; echo "${ENV_VARS[*]}")

# Step 7: Deploy to Cloud Run
echo -e "\n${CYAN}>>> Deploying to Cloud Run...${NC}"

gcloud run deploy "$SERVICE_NAME" \
    --image "gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest" \
    --platform managed \
    --region "$REGION" \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --timeout 300 \
    --max-instances 10 \
    --min-instances 0 \
    --set-env-vars "$ENV_VARS_STRING"

if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Cloud Run deployment failed!${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Deployment successful!${NC}"

# Step 8: Get service URL
echo -e "\n${CYAN}>>> Getting service URL...${NC}"
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" --region "$REGION" --format 'value(status.url)' 2>/dev/null)

if [ -n "$SERVICE_URL" ]; then
    echo -e "\n${GREEN}========================================${NC}"
    echo -e "${GREEN}  Deployment Complete!${NC}"
    echo -e "${GREEN}========================================${NC}\n"
    echo -e "Service URL: ${CYAN}${SERVICE_URL}${NC}\n"
    echo -e "${YELLOW}Next steps:${NC}"
    echo -e "  1. Visit: ${SERVICE_URL}"
    echo -e "  2. Set up Cloud SQL for persistent database"
    echo -e "  3. Configure additional environment variables if needed"
    echo -e "\nView logs: ${CYAN}gcloud run services logs read ${SERVICE_NAME} --region ${REGION}${NC}\n"
else
    echo -e "${YELLOW}⚠ Could not retrieve service URL. Check Cloud Console.${NC}\n"
fi
