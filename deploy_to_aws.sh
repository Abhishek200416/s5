#!/bin/bash
# ========================================
# Alert Whisperer AWS Deployment Script
# ========================================
# Run this script from your LOCAL COMPUTER (not from Emergent environment)
# Prerequisites: Docker installed, AWS CLI installed

set -e  # Exit on error

echo "🚀 Alert Whisperer AWS Deployment Script"
echo "=========================================="
echo ""

# Configuration
AWS_REGION="us-east-1"
AWS_ACCOUNT_ID="728925775278"
ECR_REPO_NAME="alert-whisperer-backend"
ECR_REPO_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO_NAME}"
ECS_CLUSTER="alert-whisperer-cluster"
ECS_SERVICE="alert-whisperer-backend-service"
IMAGE_TAG="latest"

echo "📋 Configuration:"
echo "   AWS Region: ${AWS_REGION}"
echo "   AWS Account: ${AWS_ACCOUNT_ID}"
echo "   ECR Repository: ${ECR_REPO_URI}"
echo "   ECS Cluster: ${ECS_CLUSTER}"
echo ""

# Step 1: Login to AWS ECR
echo "🔐 Step 1: Logging in to AWS ECR..."
aws ecr get-login-password --region ${AWS_REGION} | \
    docker login --username AWS --password-stdin ${ECR_REPO_URI}
echo "✅ ECR login successful"
echo ""

# Step 2: Build Docker image
echo "🐳 Step 2: Building Docker image..."
cd backend
docker build -t ${ECR_REPO_NAME}:${IMAGE_TAG} -f Dockerfile.production .
echo "✅ Docker image built successfully"
echo ""

# Step 3: Tag image for ECR
echo "🏷️  Step 3: Tagging image for ECR..."
docker tag ${ECR_REPO_NAME}:${IMAGE_TAG} ${ECR_REPO_URI}:${IMAGE_TAG}
echo "✅ Image tagged"
echo ""

# Step 4: Push image to ECR
echo "📤 Step 4: Pushing image to ECR..."
docker push ${ECR_REPO_URI}:${IMAGE_TAG}
echo "✅ Image pushed to ECR"
echo ""

# Step 5: Update ECS service (force new deployment)
echo "🔄 Step 5: Updating ECS service..."
aws ecs update-service \
    --cluster ${ECS_CLUSTER} \
    --service ${ECS_SERVICE} \
    --force-new-deployment \
    --region ${AWS_REGION}
echo "✅ ECS service update initiated"
echo ""

# Step 6: Wait for deployment
echo "⏳ Step 6: Waiting for deployment to complete..."
echo "   (This may take 2-3 minutes)"
aws ecs wait services-stable \
    --cluster ${ECS_CLUSTER} \
    --services ${ECS_SERVICE} \
    --region ${AWS_REGION}
echo "✅ Deployment complete!"
echo ""

# Step 7: Get service status
echo "📊 Step 7: Checking service status..."
aws ecs describe-services \
    --cluster ${ECS_CLUSTER} \
    --services ${ECS_SERVICE} \
    --region ${AWS_REGION} \
    --query 'services[0].{Status:status,Running:runningCount,Desired:desiredCount}' \
    --output table
echo ""

# Step 8: Get Load Balancer URL
echo "🌐 Step 8: Getting Load Balancer URL..."
LB_DNS=$(aws elbv2 describe-load-balancers \
    --region ${AWS_REGION} \
    --query 'LoadBalancers[?contains(LoadBalancerName, `alert-whisperer`)].DNSName' \
    --output text)

if [ -n "$LB_DNS" ]; then
    echo "✅ Load Balancer URL:"
    echo "   http://${LB_DNS}/api/companies"
    echo ""
    echo "🧪 Testing backend..."
    sleep 5  # Wait for service to be ready
    curl -s http://${LB_DNS}/api/companies | head -c 100
    echo ""
    echo "✅ Backend is responding!"
else
    echo "⚠️  Could not find Load Balancer URL"
fi

echo ""
echo "=========================================="
echo "🎉 DEPLOYMENT COMPLETE!"
echo "=========================================="
echo ""
echo "Backend URL: http://${LB_DNS}/api"
echo ""
echo "Next steps:"
echo "1. Update frontend .env with backend URL"
echo "2. Rebuild and deploy frontend to S3"
echo "3. Test the application"
echo ""
