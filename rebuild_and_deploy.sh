#!/usr/bin/env bash
set -e

echo "🚀 Alert Whisperer - Rebuild and Deploy Script"
echo "=============================================="

# Configuration
AWS_REGION="us-east-1"
AWS_ACCOUNT_ID="728925775278"
ECR_REPO_NAME="alert-whisperer-backend"
ECS_CLUSTER="alert-whisperer-cluster"
ECS_SERVICE="alert-whisperer-backend-svc"
IMAGE_TAG="latest"

# Full ECR repository URI
ECR_REPO_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO_NAME}"

echo ""
echo "📋 Configuration:"
echo "  AWS Region: ${AWS_REGION}"
echo "  AWS Account: ${AWS_ACCOUNT_ID}"
echo "  ECR Repository: ${ECR_REPO_NAME}"
echo "  ECS Cluster: ${ECS_CLUSTER}"
echo "  ECS Service: ${ECS_SERVICE}"
echo ""

# Step 1: Login to ECR
echo "🔐 Step 1: Logging in to Amazon ECR..."
aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_REPO_URI}

# Step 2: Build Docker image
echo ""
echo "🏗️  Step 2: Building Docker image..."
cd /app/backend
docker build -f Dockerfile.production -t ${ECR_REPO_NAME}:${IMAGE_TAG} .

# Step 3: Tag image for ECR
echo ""
echo "🏷️  Step 3: Tagging image for ECR..."
docker tag ${ECR_REPO_NAME}:${IMAGE_TAG} ${ECR_REPO_URI}:${IMAGE_TAG}

# Step 4: Push to ECR
echo ""
echo "📤 Step 4: Pushing image to ECR..."
docker push ${ECR_REPO_URI}:${IMAGE_TAG}

# Step 5: Force new deployment in ECS
echo ""
echo "🔄 Step 5: Forcing new ECS deployment..."
aws ecs update-service \
    --cluster ${ECS_CLUSTER} \
    --service ${ECS_SERVICE} \
    --force-new-deployment \
    --region ${AWS_REGION}

echo ""
echo "✅ Deployment initiated successfully!"
echo ""
echo "📊 Monitor deployment status:"
echo "   aws ecs describe-services --cluster ${ECS_CLUSTER} --services ${ECS_SERVICE} --region ${AWS_REGION}"
echo ""
echo "📝 View logs:"
echo "   aws logs tail /ecs/alert-whisperer-backend --follow --region ${AWS_REGION}"
echo ""
echo "🔗 Backend URL: http://alertw-alb-1475356777.us-east-1.elb.amazonaws.com/api"
echo "🔗 Frontend URL: http://alert-whisperer-frontend-728925775278.s3-website-us-east-1.amazonaws.com"
echo ""
