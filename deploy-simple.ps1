# SIMPLE 3-STEP COMPLETION SCRIPT
# You already created infrastructure, just need to:
# 1. Build & push Docker image
# 2. Register task definition  
# 3. Create service

$AccountId = "728925775278"
$Region = "us-east-1"
$Image = "${AccountId}.dkr.ecr.${Region}.amazonaws.com/alert-whisperer-backend:latest"

Write-Host ""
Write-Host "=== STEP 1: Build & Push Docker Image ===" -ForegroundColor Cyan

# ECR Login
Write-Host "Logging into ECR..." -ForegroundColor Yellow
aws ecr get-login-password --region $Region | docker login --username AWS --password-stdin "${AccountId}.dkr.ecr.${Region}.amazonaws.com"

# Build
Write-Host "Building Docker image..." -ForegroundColor Yellow
docker build -t alert-whisperer-backend:latest -f Dockerfile.production .

# Tag
Write-Host "Tagging image..." -ForegroundColor Yellow
docker tag alert-whisperer-backend:latest $Image

# Push
Write-Host "Pushing to ECR..." -ForegroundColor Yellow
docker push $Image
Write-Host "✅ Image pushed!" -ForegroundColor Green
Write-Host ""

Write-Host "=== STEP 2: Register Task Definition ===" -ForegroundColor Cyan

# Create clean JSON without PowerShell variable issues
@"
{
  "family": "alert-whisperer-backend",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::728925775278:role/alert-whisperer-ecs-execution-role",
  "taskRoleArn": "arn:aws:iam::728925775278:role/alert-whisperer-ecs-task-role",
  "containerDefinitions": [{
    "name": "alert-whisperer-backend",
    "image": "728925775278.dkr.ecr.us-east-1.amazonaws.com/alert-whisperer-backend:latest",
    "portMappings": [{"containerPort": 8001}],
    "essential": true,
    "environment": [
      {"name": "AWS_REGION", "value": "us-east-1"},
      {"name": "USE_DYNAMODB", "value": "true"},
      {"name": "DYNAMODB_TABLE_PREFIX", "value": "AlertWhisperer_"},
      {"name": "PORT", "value": "8001"}
    ],
    "logConfiguration": {
      "logDriver": "awslogs",
      "options": {
        "awslogs-group": "/ecs/alert-whisperer-backend",
        "awslogs-region": "us-east-1",
        "awslogs-stream-prefix": "ecs",
        "awslogs-create-group": "true"
      }
    }
  }]
}
"@ | Out-File -Encoding ASCII task.json

Write-Host "Registering task..." -ForegroundColor Yellow
aws ecs register-task-definition --cli-input-json file://task.json | Out-Null
Write-Host "✅ Task registered!" -ForegroundColor Green
Write-Host ""

Write-Host "=== STEP 3: Create Service ===" -ForegroundColor Cyan

# Get your infrastructure IDs
$TgArn = "arn:aws:elasticloadbalancing:us-east-1:728925775278:targetgroup/alertw-tg/0b062acb2c2adfda"
$Subnet1 = "subnet-0fefe02a847835e35"
$Subnet2 = "subnet-05d301a1db1c9ba45"
$SvcSg = (aws ec2 describe-security-groups --filters Name=group-name,Values=alertw-svc-sg --query "SecurityGroups[0].GroupId" --output text)

Write-Host "Creating ECS service..." -ForegroundColor Yellow
aws ecs create-service `
  --cluster alert-whisperer-cluster `
  --service-name alert-whisperer-backend-svc `
  --task-definition alert-whisperer-backend `
  --desired-count 1 `
  --launch-type FARGATE `
  --network-configuration "awsvpcConfiguration={subnets=[$Subnet1,$Subnet2],securityGroups=[$SvcSg],assignPublicIp=ENABLED}" `
  --load-balancers "[{targetGroupArn=$TgArn,containerName=alert-whisperer-backend,containerPort=8001}]"

Write-Host "✅ Service created!" -ForegroundColor Green
Write-Host ""

$AlbDns = "alertw-alb-1475356777.us-east-1.elb.amazonaws.com"
Write-Host "=== DONE! ===" -ForegroundColor Green
Write-Host "Backend URL: http://$AlbDns/api" -ForegroundColor Yellow
Write-Host ""
Write-Host "Wait 2-3 minutes, then test:" -ForegroundColor Yellow
Write-Host "  curl http://$AlbDns/api/companies" -ForegroundColor White
Write-Host ""
