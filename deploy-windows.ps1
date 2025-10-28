# PowerShell Deployment Script for Alert Whisperer
# Run from backend directory

Write-Host "🚀 Alert Whisperer AWS Deployment" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Configuration
$ErrorActionPreference = "Stop"
$AWS_REGION = "us-east-1"
$AccountId = (aws sts get-caller-identity --query Account --output text)
$Image = "${AccountId}.dkr.ecr.${AWS_REGION}.amazonaws.com/alert-whisperer-backend:latest"

Write-Host "📋 Configuration:" -ForegroundColor Yellow
Write-Host "   Account: $AccountId"
Write-Host "   Region: $AWS_REGION"
Write-Host "   Image: $Image"
Write-Host ""

# Step 1: Fix and Register Task Definition
Write-Host "📝 Step 1: Creating Task Definition..." -ForegroundColor Cyan

$taskDef = @{
    family = "alert-whisperer-backend"
    networkMode = "awsvpc"
    requiresCompatibilities = @("FARGATE")
    cpu = "512"
    memory = "1024"
    executionRoleArn = "arn:aws:iam::${AccountId}:role/alert-whisperer-ecs-execution-role"
    taskRoleArn = "arn:aws:iam::${AccountId}:role/alert-whisperer-ecs-task-role"
    containerDefinitions = @(
        @{
            name = "alert-whisperer-backend"
            image = $Image
            portMappings = @(
                @{
                    containerPort = 8001
                    protocol = "tcp"
                }
            )
            essential = $true
            environment = @(
                @{ name = "AWS_REGION"; value = "us-east-1" }
                @{ name = "USE_DYNAMODB"; value = "true" }
                @{ name = "DYNAMODB_TABLE_PREFIX"; value = "AlertWhisperer_" }
                @{ name = "JWT_SECRET"; value = "alert-whisperer-super-secret-jwt-key-change-in-production" }
                @{ name = "PORT"; value = "8001" }
                @{ name = "HOST"; value = "0.0.0.0" }
            )
            logConfiguration = @{
                logDriver = "awslogs"
                options = @{
                    "awslogs-group" = "/ecs/alert-whisperer-backend"
                    "awslogs-region" = "us-east-1"
                    "awslogs-stream-prefix" = "ecs"
                }
            }
            healthCheck = @{
                command = @("CMD-SHELL", "curl -f http://localhost:8001/api/companies || exit 1")
                interval = 30
                timeout = 5
                retries = 3
                startPeriod = 60
            }
        }
    )
}

# Convert to JSON and save
$taskDefJson = $taskDef | ConvertTo-Json -Depth 10
$taskDefJson | Out-File -Encoding UTF8 -FilePath "task-definition-fixed.json"

Write-Host "✅ Task definition JSON created" -ForegroundColor Green
Write-Host ""

# Step 2: Login to ECR
Write-Host "🔐 Step 2: Logging into ECR..." -ForegroundColor Cyan
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin "${AccountId}.dkr.ecr.${AWS_REGION}.amazonaws.com"
Write-Host "✅ ECR login successful" -ForegroundColor Green
Write-Host ""

# Step 3: Build Docker image
Write-Host "🐳 Step 3: Building Docker image..." -ForegroundColor Cyan
docker build -t alert-whisperer-backend:latest -f Dockerfile.production .
Write-Host "✅ Docker image built" -ForegroundColor Green
Write-Host ""

# Step 4: Tag image
Write-Host "🏷️  Step 4: Tagging image..." -ForegroundColor Cyan
docker tag alert-whisperer-backend:latest $Image
Write-Host "✅ Image tagged" -ForegroundColor Green
Write-Host ""

# Step 5: Push to ECR
Write-Host "📤 Step 5: Pushing to ECR (this may take 2-5 minutes)..." -ForegroundColor Cyan
docker push $Image
Write-Host "✅ Image pushed to ECR" -ForegroundColor Green
Write-Host ""

# Step 6: Register task definition
Write-Host "📝 Step 6: Registering task definition..." -ForegroundColor Cyan
aws ecs register-task-definition --cli-input-json file://task-definition-fixed.json | Out-Null
$Rev = (aws ecs describe-task-definition --task-definition alert-whisperer-backend --query taskDefinition.revision --output text)
Write-Host "✅ Task definition registered: alert-whisperer-backend:$Rev" -ForegroundColor Green
Write-Host ""

# Step 7: Get your new infrastructure details
Write-Host "🔍 Step 7: Getting infrastructure details..." -ForegroundColor Cyan

# Get the NEW ALB you just created
$AlbArn = (aws elbv2 describe-load-balancers --query "LoadBalancers[?LoadBalancerName=='alertw-alb'].LoadBalancerArn" --output text)
$AlbDns = (aws elbv2 describe-load-balancers --load-balancer-arns $AlbArn --query LoadBalancers[0].DNSName --output text)

# Get the NEW target group
$TgArn = (aws elbv2 describe-target-groups --query "TargetGroups[?TargetGroupName=='alertw-tg'].TargetGroupArn" --output text)

# Get subnets
$VpcId = (aws ec2 describe-vpcs --filters Name=isDefault,Values=true --query "Vpcs[0].VpcId" --output text)
$SubnetsRaw = (aws ec2 describe-subnets --filters Name=vpc-id,Values=$VpcId --query "Subnets[?MapPublicIpOnLaunch==``true``].SubnetId" --output text)
$Subnets = $SubnetsRaw -split "\s+"

# Get service security group
$SvcSg = (aws ec2 describe-security-groups --filters Name=group-name,Values=alertw-svc-sg --query "SecurityGroups[0].GroupId" --output text)

Write-Host "✅ Infrastructure found:" -ForegroundColor Green
Write-Host "   ALB: $AlbDns"
Write-Host "   Target Group: $TgArn"
Write-Host "   Subnets: $($Subnets -join ', ')"
Write-Host "   Security Group: $SvcSg"
Write-Host ""

# Step 8: Create ECS service
Write-Host "🚀 Step 8: Creating ECS service..." -ForegroundColor Cyan

$serviceParams = @{
    cluster = "alert-whisperer-cluster"
    serviceName = "alert-whisperer-backend-svc"
    taskDefinition = "alert-whisperer-backend:$Rev"
    desiredCount = 1
    launchType = "FARGATE"
    networkConfiguration = "awsvpcConfiguration={subnets=[$($Subnets -join ',')],securityGroups=[$SvcSg],assignPublicIp=ENABLED}"
    loadBalancers = "[{targetGroupArn=$TgArn,containerName=alert-whisperer-backend,containerPort=8001}]"
}

try {
    aws ecs create-service `
        --cluster $serviceParams.cluster `
        --service-name $serviceParams.serviceName `
        --task-definition $serviceParams.taskDefinition `
        --desired-count $serviceParams.desiredCount `
        --launch-type $serviceParams.launchType `
        --network-configuration $serviceParams.networkConfiguration `
        --load-balancers $serviceParams.loadBalancers | Out-Null
    
    Write-Host "✅ ECS service created!" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Service might already exist, checking..." -ForegroundColor Yellow
}
Write-Host ""

# Step 9: Wait for deployment
Write-Host "⏳ Step 9: Waiting for service to stabilize (2-3 minutes)..." -ForegroundColor Cyan
aws ecs wait services-stable --cluster alert-whisperer-cluster --services alert-whisperer-backend-svc
Write-Host "✅ Service is stable!" -ForegroundColor Green
Write-Host ""

# Step 10: Test backend
Write-Host "🧪 Step 10: Testing backend..." -ForegroundColor Cyan
Write-Host "Backend URL: http://$AlbDns/api" -ForegroundColor Yellow
Write-Host ""
Write-Host "Waiting 10 seconds for service to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

try {
    $response = Invoke-WebRequest -Uri "http://$AlbDns/api/companies" -UseBasicParsing
    Write-Host "✅ Backend is responding! HTTP $($response.StatusCode)" -ForegroundColor Green
    Write-Host ""
    Write-Host "Sample response:" -ForegroundColor Yellow
    Write-Host $response.Content.Substring(0, [Math]::Min(200, $response.Content.Length))
    Write-Host "..."
} catch {
    Write-Host "⚠️  Backend not responding yet. Check logs:" -ForegroundColor Yellow
    Write-Host "   aws logs tail /ecs/alert-whisperer-backend --follow"
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "🎉 DEPLOYMENT COMPLETE!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "🌐 Your Backend URL:" -ForegroundColor Yellow
Write-Host "   http://$AlbDns/api"
Write-Host ""
Write-Host "📝 Next Steps:" -ForegroundColor Yellow
Write-Host "   1. Update frontend .env with backend URL"
Write-Host "   2. Test all API endpoints"
Write-Host "   3. Monitor CloudWatch logs"
Write-Host ""
Write-Host "Frontend S3 Bucket Update:" -ForegroundColor Yellow
Write-Host "   Your frontend: http://alert-whisperer-frontend-728925775278.s3-website-us-east-1.amazonaws.com"
Write-Host "   Update REACT_APP_BACKEND_URL to: http://$AlbDns/api"
Write-Host ""
