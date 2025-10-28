#!/usr/bin/env python3
"""
Quick deployment helper - checks what needs to be done
"""
import boto3
import os
import sys
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
ROOT_DIR = Path(__file__).parent / 'backend'
load_dotenv(ROOT_DIR / '.env')

AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
AWS_ACCESS_KEY_ID=[REDACTED]
AWS_SECRET_ACCESS_KEY=[REDACTED]
AWS_SESSION_TOKEN=[REDACTED]

session = boto3.Session(
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    aws_session_token=AWS_SESSION_TOKEN,
    region_name=AWS_REGION
)

print("🔍 Checking ECS Service Status...")
print()

try:
    ecs = session.client('ecs')
    
    # Check if service exists
    response = ecs.describe_services(
        cluster='alert-whisperer-cluster',
        services=['alert-whisperer-backend-service']
    )
    
    if response['services'] and response['services'][0]['status'] != 'INACTIVE':
        service = response['services'][0]
        print("✅ ECS Service EXISTS")
        print(f"   Status: {service['status']}")
        print(f"   Running: {service['runningCount']}/{service['desiredCount']}")
        print(f"   Task Definition: {service['taskDefinition'].split('/')[-1]}")
        print()
        print("📋 Deployment Steps:")
        print("   1. Build Docker image locally")
        print("   2. Push to ECR")
        print("   3. Update service with: aws ecs update-service --cluster alert-whisperer-cluster --service alert-whisperer-backend-service --force-new-deployment")
        print()
        
        # Get current task definition
        task_def_arn = service['taskDefinition']
        task_def = ecs.describe_task_definition(taskDefinition=task_def_arn)
        container = task_def['taskDefinition']['containerDefinitions'][0]
        current_image = container['image']
        print(f"   Current Image: {current_image}")
        print()
        
    else:
        print("❌ ECS Service DOES NOT EXIST")
        print()
        print("📋 Deployment Steps:")
        print("   1. Register task definition")
        print("   2. Build Docker image")
        print("   3. Push to ECR")
        print("   4. Create ECS service with load balancer")
        print()
        print("Run these commands:")
        print()
        print("   # Register task definition")
        print("   aws ecs register-task-definition --cli-input-json file://backend/task-definition.json")
        print()
        print("   # Get target group ARN")
        print('   aws elbv2 describe-target-groups --query "TargetGroups[?contains(TargetGroupName, \'alert\')].TargetGroupArn" --output text')
        print()
        print("   # Create service (replace TARGET_GROUP_ARN)")
        print("   aws ecs create-service \\")
        print("       --cluster alert-whisperer-cluster \\")
        print("       --service-name alert-whisperer-backend-service \\")
        print("       --task-definition alert-whisperer-backend:1 \\")
        print("       --desired-count 1 \\")
        print("       --launch-type FARGATE \\")
        print('       --network-configuration "awsvpcConfiguration={subnets=[subnet-0fefe02a847835e35,subnet-05d301a1db1c9ba45],securityGroups=[sg-0bab78f004d290e50],assignPublicIp=ENABLED}" \\')
        print('       --load-balancers "targetGroupArn=TARGET_GROUP_ARN,containerName=alert-whisperer-backend,containerPort=8001"')
        print()
    
    # Check if target group exists
    elbv2 = session.client('elbv2')
    tgs = elbv2.describe_target_groups()
    alert_tgs = [tg for tg in tgs['TargetGroups'] if 'alert' in tg['TargetGroupName'].lower()]
    
    if alert_tgs:
        print("🎯 Target Groups Found:")
        for tg in alert_tgs:
            print(f"   - {tg['TargetGroupName']}: {tg['TargetGroupArn']}")
            
            # Check target health
            health = elbv2.describe_target_health(TargetGroupArn=tg['TargetGroupArn'])
            if health['TargetHealthDescriptions']:
                for target in health['TargetHealthDescriptions']:
                    state = target['TargetHealth']['State']
                    emoji = "✅" if state == "healthy" else "⚠️" if state == "initial" else "❌"
                    print(f"     {emoji} {target['Target']['Id']}: {state}")
            else:
                print(f"     ⚠️  No targets registered")
        print()
    
    # Get load balancer URL
    lbs = elbv2.describe_load_balancers()
    alert_lbs = [lb for lb in lbs['LoadBalancers'] if 'alert' in lb['LoadBalancerName'].lower()]
    
    if alert_lbs:
        lb = alert_lbs[0]
        print(f"🌐 Load Balancer URL:")
        print(f"   http://{lb['DNSName']}/api/companies")
        print()
        print(f"   Test with: curl http://{lb['DNSName']}/api/companies")
        print()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("✅ Check complete!")
