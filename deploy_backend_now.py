#!/usr/bin/env python3
"""
Deploy Alert Whisperer Backend to AWS ECS
"""
import boto3
import os
import json
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
ROOT_DIR = Path(__file__).parent / 'backend'
load_dotenv(ROOT_DIR / '.env')

AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
AWS_ACCESS_KEY_ID=[REDACTED]
AWS_SECRET_ACCESS_KEY=[REDACTED]
AWS_SESSION_TOKEN=[REDACTED]

print("🚀 Deploying Alert Whisperer Backend to AWS ECS")
print("=" * 60)
print()

# Create boto3 session
session = boto3.Session(
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    aws_session_token=AWS_SESSION_TOKEN,
    region_name=AWS_REGION
)

try:
    # Verify credentials
    sts = session.client('sts')
    identity = sts.get_caller_identity()
    account_id = identity['Account']
    print(f"✅ AWS Account: {account_id}")
    print(f"✅ User: {identity['Arn']}")
    print()
    
    # Step 1: Check if Docker image exists in ECR
    print("📦 Step 1: Checking ECR for Docker image...")
    ecr = session.client('ecr')
    
    try:
        images = ecr.describe_images(
            repositoryName='alert-whisperer-backend',
            imageIds=[{'imageTag': 'latest'}]
        )
        print(f"✅ Docker image found in ECR: alert-whisperer-backend:latest")
        image_uri = f"{account_id}.dkr.ecr.{AWS_REGION}.amazonaws.com/alert-whisperer-backend:latest"
    except ecr.exceptions.ImageNotFoundException:
        print("⚠️  No Docker image found in ECR")
        print("   You need to build and push the Docker image first:")
        print()
        print("   From your computer, run:")
        print(f"   aws ecr get-login-password --region {AWS_REGION} | docker login --username AWS --password-stdin {account_id}.dkr.ecr.{AWS_REGION}.amazonaws.com")
        print("   docker build -t alert-whisperer-backend:latest -f Dockerfile.production .")
        print(f"   docker tag alert-whisperer-backend:latest {account_id}.dkr.ecr.{AWS_REGION}.amazonaws.com/alert-whisperer-backend:latest")
        print(f"   docker push {account_id}.dkr.ecr.{AWS_REGION}.amazonaws.com/alert-whisperer-backend:latest")
        print()
        print("❌ Cannot proceed without Docker image. Please build and push first.")
        exit(1)
    
    print()
    
    # Step 2: Register Task Definition
    print("📝 Step 2: Registering ECS Task Definition...")
    ecs = session.client('ecs')
    
    task_definition = {
        'family': 'alert-whisperer-backend',
        'networkMode': 'awsvpc',
        'requiresCompatibilities': ['FARGATE'],
        'cpu': '512',
        'memory': '1024',
        'executionRoleArn': f'arn:aws:iam::{account_id}:role/alert-whisperer-ecs-execution-role',
        'taskRoleArn': f'arn:aws:iam::{account_id}:role/alert-whisperer-ecs-task-role',
        'containerDefinitions': [
            {
                'name': 'alert-whisperer-backend',
                'image': image_uri,
                'portMappings': [
                    {
                        'containerPort': 8001,
                        'protocol': 'tcp'
                    }
                ],
                'essential': True,
                'environment': [
                    {'name': 'AWS_REGION', 'value': 'us-east-1'},
                    {'name': 'USE_DYNAMODB', 'value': 'true'},
                    {'name': 'DYNAMODB_TABLE_PREFIX', 'value': 'AlertWhisperer_'},
                    {'name': 'JWT_SECRET', 'value': 'alert-whisperer-super-secret-jwt-key-change-in-production'},
                    {'name': 'PORT', 'value': '8001'},
                    {'name': 'HOST', 'value': '0.0.0.0'}
                ],
                'logConfiguration': {
                    'logDriver': 'awslogs',
                    'options': {
                        'awslogs-group': '/ecs/alert-whisperer-backend',
                        'awslogs-region': 'us-east-1',
                        'awslogs-stream-prefix': 'ecs',
                        'awslogs-create-group': 'true'
                    }
                },
                'healthCheck': {
                    'command': ['CMD-SHELL', 'curl -f http://localhost:8001/api/companies || exit 1'],
                    'interval': 30,
                    'timeout': 5,
                    'retries': 3,
                    'startPeriod': 60
                }
            }
        ]
    }
    
    response = ecs.register_task_definition(**task_definition)
    revision = response['taskDefinition']['revision']
    print(f"✅ Task definition registered: alert-whisperer-backend:{revision}")
    print()
    
    # Step 3: Get Infrastructure Details
    print("🔍 Step 3: Getting infrastructure details...")
    
    # Get target group
    elbv2 = session.client('elbv2')
    target_groups = elbv2.describe_target_groups()
    alertw_tg = [tg for tg in target_groups['TargetGroups'] if tg['TargetGroupName'] == 'alertw-tg']
    
    if not alertw_tg:
        print("❌ Target group 'alertw-tg' not found")
        exit(1)
    
    target_group_arn = alertw_tg[0]['TargetGroupArn']
    print(f"✅ Target Group: {target_group_arn}")
    
    # Get subnets
    ec2 = session.client('ec2')
    vpcs = ec2.describe_vpcs(Filters=[{'Name': 'isDefault', 'Values': ['true']}])
    vpc_id = vpcs['Vpcs'][0]['VpcId']
    
    subnets = ec2.describe_subnets(
        Filters=[
            {'Name': 'vpc-id', 'Values': [vpc_id]},
            {'Name': 'map-public-ip-on-launch', 'Values': ['true']}
        ]
    )
    subnet_ids = [s['SubnetId'] for s in subnets['Subnets'][:2]]
    print(f"✅ Subnets: {', '.join(subnet_ids)}")
    
    # Get security group
    sgs = ec2.describe_security_groups(Filters=[{'Name': 'group-name', 'Values': ['alertw-svc-sg']}])
    if not sgs['SecurityGroups']:
        print("❌ Security group 'alertw-svc-sg' not found")
        exit(1)
    
    security_group_id = sgs['SecurityGroups'][0]['GroupId']
    print(f"✅ Security Group: {security_group_id}")
    print()
    
    # Step 4: Check if service exists
    print("🔍 Step 4: Checking if ECS service exists...")
    
    try:
        services = ecs.describe_services(
            cluster='alert-whisperer-cluster',
            services=['alert-whisperer-backend-svc']
        )
        
        if services['services'] and services['services'][0]['status'] == 'ACTIVE':
            print("⚠️  Service already exists. Updating...")
            
            # Update service
            ecs.update_service(
                cluster='alert-whisperer-cluster',
                service='alert-whisperer-backend-svc',
                taskDefinition=f'alert-whisperer-backend:{revision}',
                forceNewDeployment=True
            )
            print("✅ Service updated with new task definition")
        else:
            raise Exception("Service needs to be created")
            
    except Exception as e:
        print("Creating new service...")
        
        # Step 5: Create Service
        print("🚀 Step 5: Creating ECS service...")
        
        try:
            response = ecs.create_service(
                cluster='alert-whisperer-cluster',
                serviceName='alert-whisperer-backend-svc',
                taskDefinition=f'alert-whisperer-backend:{revision}',
                desiredCount=1,
                launchType='FARGATE',
                networkConfiguration={
                    'awsvpcConfiguration': {
                        'subnets': subnet_ids,
                        'securityGroups': [security_group_id],
                        'assignPublicIp': 'ENABLED'
                    }
                },
                loadBalancers=[
                    {
                        'targetGroupArn': target_group_arn,
                        'containerName': 'alert-whisperer-backend',
                        'containerPort': 8001
                    }
                ]
            )
            print("✅ ECS service created successfully!")
        except Exception as create_error:
            print(f"⚠️  Error creating service: {create_error}")
            print("   Service might already exist or there's a configuration issue")
    
    print()
    
    # Step 6: Get Load Balancer DNS
    print("🌐 Step 6: Getting Load Balancer URL...")
    
    lbs = elbv2.describe_load_balancers()
    alertw_lb = [lb for lb in lbs['LoadBalancers'] if 'alertw-alb' in lb['LoadBalancerName']]
    
    if alertw_lb:
        lb_dns = alertw_lb[0]['DNSName']
        print(f"✅ Load Balancer DNS: {lb_dns}")
        print()
        
        print("=" * 60)
        print("🎉 BACKEND DEPLOYMENT INITIATED!")
        print("=" * 60)
        print()
        print(f"🌐 Backend URL:")
        print(f"   http://{lb_dns}/api")
        print()
        print("⏳ Service is starting (wait 2-3 minutes for tasks to be healthy)")
        print()
        print("🧪 Test with:")
        print(f"   curl http://{lb_dns}/api/companies")
        print()
        print("📊 Monitor deployment:")
        print("   aws ecs describe-services --cluster alert-whisperer-cluster --services alert-whisperer-backend-svc")
        print()
        print("📜 View logs:")
        print("   aws logs tail /ecs/alert-whisperer-backend --follow")
        print()
        print("🎯 Next Step:")
        print(f"   Update frontend .env with: REACT_APP_BACKEND_URL=http://{lb_dns}/api")
        print()
    else:
        print("⚠️  Load balancer not found")
    
except Exception as e:
    print(f"❌ Deployment failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
