# Quick Fix Script - Register Task Definition and Create Service
# Run this from backend directory after Docker image is pushed

Write-Host "🔧 Quick Fix: Task Definition + Service Creation" -ForegroundColor Cyan
Write-Host ""

$AccountId = (aws sts get-caller-identity --query Account --output text)
$Image = "${AccountId}.dkr.ecr.us-east-1.amazonaws.com/alert-whisperer-backend:latest"

# Create proper task definition JSON
$taskDef = @"
{
  "family": "alert-whisperer-backend",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::${AccountId}:role/alert-whisperer-ecs-execution-role",
  "taskRoleArn": "arn:aws:iam::${AccountId}:role/alert-whisperer-ecs-task-role",
  "containerDefinitions": [{
    "name": "alert-whisperer-backend",
    "image": "$Image",
    "portMappings": [{"containerPort": 8001, "protocol": "tcp"}],
    "essential": true,
    "environment": [
      {"name": "AWS_REGION", "value": "us-east-1"},
      {"name": "USE_DYNAMODB", "value": "true"},
      {"name": "DYNAMODB_TABLE_PREFIX", "value": "AlertWhisperer_"},
      {"name": "JWT_SECRET", "value": "alert-whisperer-super-secret-jwt-key-change-in-production"},
      {"name": "PORT", "value": "8001"},
      {"name": "HOST", "value": "0.0.0.0"}
    ],
    "logConfiguration": {
      "logDriver": "awslogs",
      "options": {
        "awslogs-group": "/ecs/alert-whisperer-backend",
        "awslogs-region": "us-east-1",
        "awslogs-stream-prefix": "ecs",
        "awslogs-create-group": "true"
      }
    },
    "healthCheck": {
      "command": ["CMD-SHELL", "curl -f http://localhost:8001/api/companies || exit 1"],
      "interval": 30,
      "timeout": 5,
      "retries": 3,
      "startPeriod": 60
    }
  }]
}
"@

Write-Host "📝 Creating task definition file..." -ForegroundColor Yellow
$taskDef | Out-File -Encoding UTF8 -FilePath "task-def-final.json"
Write-Host "✅ File created: task-def-final.json" -ForegroundColor Green
Write-Host ""

Write-Host "📝 Registering task definition..." -ForegroundColor Yellow
aws ecs register-task-definition --cli-input-json file://task-def-final.json | Out-Null
$Rev = (aws ecs describe-task-definition --task-definition alert-whisperer-backend --query taskDefinition.revision --output text)
Write-Host "✅ Task registered: alert-whisperer-backend:$Rev" -ForegroundColor Green
Write-Host ""

# Get infrastructure details
Write-Host "🔍 Getting infrastructure details..." -ForegroundColor Yellow
$TgArn = (aws elbv2 describe-target-groups --query "TargetGroups[?TargetGroupName=='alertw-tg'].TargetGroupArn" --output text)
$VpcId = (aws ec2 describe-vpcs --filters Name=isDefault,Values=true --query "Vpcs[0].VpcId" --output text)
$SubnetsRaw = (aws ec2 describe-subnets --filters Name=vpc-id,Values=$VpcId Name=map-public-ip-on-launch,Values=true --query "Subnets[].SubnetId" --output text)
$Subnets = $SubnetsRaw -split "\s+" | Select-Object -First 2
$SvcSg = (aws ec2 describe-security-groups --filters Name=group-name,Values=alertw-svc-sg --query "SecurityGroups[0].GroupId" --output text)

Write-Host "   Target Group: $TgArn" -ForegroundColor White
Write-Host "   Subnets: $($Subnets -join ', ')" -ForegroundColor White
Write-Host "   Security Group: $SvcSg" -ForegroundColor White
Write-Host ""

# Create service
Write-Host "🚀 Creating ECS service..." -ForegroundColor Yellow

$cmd = @"
aws ecs create-service ``
  --cluster alert-whisperer-cluster ``
  --service-name alert-whisperer-backend-svc ``
  --task-definition alert-whisperer-backend:$Rev ``
  --desired-count 1 ``
  --launch-type FARGATE ``
  --network-configuration "awsvpcConfiguration={subnets=[$($Subnets -join ',')],securityGroups=[$SvcSg],assignPublicIp=ENABLED}" ``
  --load-balancers "[{targetGroupArn=$TgArn,containerName=alert-whisperer-backend,containerPort=8001}]"
"@

Write-Host $cmd -ForegroundColor Gray
Write-Host ""

try {
    Invoke-Expression $cmd | Out-Null
    Write-Host "✅ Service created successfully!" -ForegroundColor Green
} catch {
    if ($_.Exception.Message -like "*already exists*") {
        Write-Host "⚠️  Service already exists. Updating instead..." -ForegroundColor Yellow
        aws ecs update-service --cluster alert-whisperer-cluster --service alert-whisperer-backend-svc --force-new-deployment | Out-Null
        Write-Host "✅ Service updated!" -ForegroundColor Green
    } else {
        Write-Host "❌ Error: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
}
Write-Host ""

# Get ALB DNS
$AlbDns = (aws elbv2 describe-load-balancers --query "LoadBalancers[?LoadBalancerName=='alertw-alb'].DNSName" --output text)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "🎉 Setup Complete!" -ForegroundColor Green  
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "🌐 Backend URL:" -ForegroundColor Yellow
Write-Host "   http://$AlbDns/api"
Write-Host ""
Write-Host "⏳ Service is starting (wait 2-3 minutes)" -ForegroundColor Yellow
Write-Host ""
Write-Host "📊 Check status:" -ForegroundColor Yellow
Write-Host "   aws ecs describe-services --cluster alert-whisperer-cluster --services alert-whisperer-backend-svc"
Write-Host ""
Write-Host "📜 View logs:" -ForegroundColor Yellow
Write-Host "   aws logs tail /ecs/alert-whisperer-backend --follow"
Write-Host ""
