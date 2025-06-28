#!/bin/bash

# Deploy Manim Studio AI to Google Cloud Run
# Usage: ./deploy.sh [PROJECT_ID] [REGION]

set -e

PROJECT_ID=${1:-"your-gcp-project-id"}
REGION=${2:-"us-central1"}

echo "🚀 Deploying Manim Studio AI to Google Cloud Platform"
echo "Project ID: $PROJECT_ID"
echo "Region: $REGION"

# Authenticate and set project
gcloud auth application-default login
gcloud config set project $PROJECT_ID

# Enable required APIs
echo "📋 Enabling required APIs..."
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable containerregistry.googleapis.com

# Create secrets (you'll need to set these values)
echo "🔐 Creating secrets..."
echo "Note: You'll need to update these secrets with your actual values"

# Create placeholder secrets (replace with actual values)
printf "your-actual-gemini-api-key" | gcloud secrets create gemini-api-key --data-file=-
printf "your-supabase-url" | gcloud secrets create supabase-url --data-file=-
printf "your-supabase-anon-key" | gcloud secrets create supabase-anon-key --data-file=-
printf "your-stripe-secret-key" | gcloud secrets create stripe-secret-key --data-file=-
printf "your-stripe-publishable-key" | gcloud secrets create stripe-publishable-key --data-file=-

# Grant access to secrets
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

# Build and deploy manim worker
echo "🔨 Building and deploying manim worker..."
gcloud builds submit ./manim-worker \
    --tag gcr.io/$PROJECT_ID/manim-studio-worker:latest

# Deploy manim worker
sed "s/PROJECT_ID/$PROJECT_ID/g" manim-worker-cloudrun.yaml > manim-worker-deploy.yaml
gcloud run services replace manim-worker-deploy.yaml --region=$REGION

# Get manim worker URL
WORKER_URL=$(gcloud run services describe manim-studio-worker --region=$REGION --format="value(status.url)")
echo "Manim Worker URL: $WORKER_URL"

# Build and deploy backend
echo "🔨 Building and deploying backend..."
gcloud builds submit ./backend \
    --tag gcr.io/$PROJECT_ID/manim-studio-backend:latest

# Update backend config with worker URL
sed "s/PROJECT_ID/$PROJECT_ID/g" backend-cloudrun.yaml | \
sed "s|https://manim-studio-worker-SERVICE_HASH-uc.a.run.app|$WORKER_URL|g" > backend-deploy.yaml

# Deploy backend
gcloud run services replace backend-deploy.yaml --region=$REGION

# Get backend URL
BACKEND_URL=$(gcloud run services describe manim-studio-backend --region=$REGION --format="value(status.url)")
echo "Backend URL: $BACKEND_URL"

# Clean up temporary files
rm -f *-deploy.yaml

echo "✅ Deployment complete!"
echo ""
echo "🔧 Backend URL: $BACKEND_URL"
echo "⚙️  Worker URL: $WORKER_URL"
echo ""
echo "Next steps:"
echo "1. Update your secrets with actual values:"
echo "   - gcloud secrets versions add gemini-api-key --data-file=- < your-key-file"
echo "   - gcloud secrets versions add supabase-url --data-file=- < your-url-file"
echo "   - etc."
echo "2. Configure your domain and SSL certificates"
echo "3. Set up monitoring and logging"
echo "4. Configure Supabase and Stripe integrations"
