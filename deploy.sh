#!/bin/bash
set -e

# Configuration
PROJECT_ID=$(gcloud config get-value project)
SERVICE_NAME="slack-mcp-client"
REGION="asia-northeast1"  # Tokyo region
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Deploying ${SERVICE_NAME} to Cloud Run in ${REGION}${NC}"

# Ensure user is authenticated with Google Cloud
echo -e "${GREEN}Checking Google Cloud authentication...${NC}"
if ! gcloud auth print-access-token &>/dev/null; then
  echo -e "${RED}Not authenticated with Google Cloud. Please run:${NC}"
  echo -e "${YELLOW}gcloud auth login${NC}"
  echo -e "${YELLOW}gcloud auth configure-docker${NC}"
  exit 1
fi

# Configure Docker to use gcloud as a credential helper
echo -e "${GREEN}Configuring Docker authentication for Google Container Registry...${NC}"
gcloud auth configure-docker --quiet

# Check if .env file exists
if [ ! -f .env ]; then
  echo -e "${YELLOW}Warning: .env file not found. Creating from .env.example...${NC}"
  cp .env.example .env
  echo -e "${YELLOW}Please edit .env file with your credentials before continuing.${NC}"
  exit 1
fi

# Build the container image using buildpacks
echo -e "${GREEN}Building container image with buildpacks...${NC}"
docker build --platform=linux/amd64 -t ${SERVICE_NAME} .

# Tag the image for Google Container Registry
echo -e "${GREEN}Tagging image for Google Container Registry...${NC}"
docker tag ${SERVICE_NAME} ${IMAGE_NAME}

# Push the image to Google Container Registry
echo -e "${GREEN}Pushing image to Google Container Registry...${NC}"
docker push ${IMAGE_NAME}

if [ $? -ne 0 ]; then
  echo -e "${RED}Failed to push image to Google Container Registry.${NC}"
  echo -e "${YELLOW}Make sure you have the necessary permissions and have run:${NC}"
  echo -e "${YELLOW}gcloud auth login${NC}"
  echo -e "${YELLOW}gcloud auth configure-docker${NC}"
  exit 1
fi

# Convert .env file to the format expected by Cloud Run
echo -e "${GREEN}Processing environment variables...${NC}"
if [ -f .env ]; then
  ENV_VARS=$(grep -v '^#' .env | grep '=' | sed 's/^/--set-env-vars=/' | tr '\n' ' ' | sed 's/,$//')
  if [ -z "$ENV_VARS" ]; then
    echo -e "${YELLOW}Warning: No environment variables found in .env file${NC}"
    ENV_VARS_ARGS=""
  else
    ENV_VARS_ARGS=$ENV_VARS
  fi
else
  echo -e "${RED}Error: .env file not found${NC}"
  exit 1
fi

# Deploy to Cloud Run
echo -e "${GREEN}Deploying to Cloud Run...${NC}"
gcloud run deploy ${SERVICE_NAME} \
  --image ${IMAGE_NAME} \
  --platform managed \
  --region ${REGION} \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 10 \
  $ENV_VARS_ARGS

echo -e "${GREEN}Deployment complete!${NC}"
echo -e "Service URL: $(gcloud run services describe ${SERVICE_NAME} --region ${REGION} --format='value(status.url)')"
