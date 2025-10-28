#!/usr/bin/env python3
"""
Check AWS Infrastructure for Alert Whisperer Deployment
"""
import boto3
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# AWS Configuration
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
AWS_ACCESS_KEY_ID=[REDACTED]
AWS_SECRET_ACCESS_KEY=[REDACTED]
AWS_SESSION_TOKEN=[REDACTED]

print("🔍 Checking AWS Infrastructure for Alert Whisperer...")
print(f"📍 Region: {AWS_REGION}")
print()

# Create boto3 session
session = boto3.Session(
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    aws_session_token=AWS_SESSION_TOKEN,
    region_name=AWS_REGION
)

try:
    # 1. Check AWS Identity
    sts = session.client('sts')
    identity = sts.get_caller_identity()
    print("✅ AWS Credentials Valid!")
    print(f"   Account: {identity['Account']}")
    print(f"   User ARN: {identity['Arn']}")
    print()
    
    # 2. Check ECR Repository
    ecr = session.client('ecr')
    print("📦 Checking ECR Repository...")
    try:
        repos = ecr.describe_repositories(repositoryNames=['alert-whisperer-backend'])
        repo = repos['repositories'][0]
        print(f"✅ ECR Repository exists: {repo['repositoryUri']}")
    except ecr.exceptions.RepositoryNotFoundException:
        print("❌ ECR Repository 'alert-whisperer-backend' NOT found")
        print("   Need to create: aws ecr create-repository --repository-name alert-whisperer-backend")
    print()
    
    # 3. Check ECS Cluster
    ecs = session.client('ecs')
    print("🐳 Checking ECS Cluster...")
    try:
        clusters = ecs.describe_clusters(clusters=['alert-whisperer-cluster'])
        if clusters['clusters']:
            cluster = clusters['clusters'][0]
            print(f"✅ ECS Cluster exists: {cluster['clusterName']}")
            print(f"   Status: {cluster['status']}")
        else:
            print("❌ ECS Cluster 'alert-whisperer-cluster' NOT found")
            print("   Need to create: aws ecs create-cluster --cluster-name alert-whisperer-cluster")
    except Exception as e:
        print(f"❌ Error checking cluster: {e}")
    print()
    
    # 4. Check Load Balancer
    elbv2 = session.client('elbv2')
    print("⚖️  Checking Load Balancer...")
    try:
        lbs = elbv2.describe_load_balancers()
        alert_lb = [lb for lb in lbs['LoadBalancers'] if 'alert-whisperer' in lb['LoadBalancerName'].lower()]
        if alert_lb:
            lb = alert_lb[0]
            print(f"✅ Load Balancer exists: {lb['LoadBalancerName']}")
            print(f"   DNS: {lb['DNSName']}")
        else:
            print("❌ Load Balancer 'alert-whisperer-alb' NOT found")
            print("   Need to create Application Load Balancer")
    except Exception as e:
        print(f"⚠️  Error checking load balancer: {e}")
    print()
    
    # 5. Check VPC and Subnets
    ec2 = session.client('ec2')
    print("🌐 Checking VPC and Subnets...")
    try:
        vpcs = ec2.describe_vpcs()
        default_vpc = [vpc for vpc in vpcs['Vpcs'] if vpc.get('IsDefault', False)]
        if default_vpc:
            vpc = default_vpc[0]
            print(f"✅ Default VPC found: {vpc['VpcId']}")
            
            # Check subnets
            subnets = ec2.describe_subnets(Filters=[{'Name': 'vpc-id', 'Values': [vpc['VpcId']]}])
            public_subnets = [s for s in subnets['Subnets'] if s.get('MapPublicIpOnLaunch', False)]
            print(f"✅ Found {len(subnets['Subnets'])} subnets ({len(public_subnets)} public)")
            if subnets['Subnets']:
                print(f"   Subnet IDs: {', '.join([s['SubnetId'] for s in subnets['Subnets'][:3]])}")
        else:
            print("⚠️  No default VPC found")
    except Exception as e:
        print(f"⚠️  Error checking VPC: {e}")
    print()
    
    # 6. Check Security Groups
    print("🔒 Checking Security Groups...")
    try:
        sgs = ec2.describe_security_groups()
        alert_sg = [sg for sg in sgs['SecurityGroups'] if 'alert-whisperer' in sg['GroupName'].lower()]
        if alert_sg:
            sg = alert_sg[0]
            print(f"✅ Security Group exists: {sg['GroupName']} ({sg['GroupId']})")
        else:
            print("⚠️  No 'alert-whisperer' security group found (will need to create)")
    except Exception as e:
        print(f"⚠️  Error checking security groups: {e}")
    print()
    
    # 7. Check DynamoDB Tables
    dynamodb = session.client('dynamodb')
    print("🗄️  Checking DynamoDB Tables...")
    try:
        tables = dynamodb.list_tables()
        alert_tables = [t for t in tables['TableNames'] if t.startswith('AlertWhisperer_')]
        if alert_tables:
            print(f"✅ Found {len(alert_tables)} DynamoDB tables:")
            for table in alert_tables[:5]:
                print(f"   - {table}")
            if len(alert_tables) > 5:
                print(f"   ... and {len(alert_tables) - 5} more")
        else:
            print("⚠️  No AlertWhisperer DynamoDB tables found")
    except Exception as e:
        print(f"⚠️  Error checking DynamoDB: {e}")
    print()
    
    # Summary
    print("=" * 60)
    print("📊 INFRASTRUCTURE SUMMARY")
    print("=" * 60)
    print("✅ AWS Credentials: Valid")
    print("📦 ECR Repository: Check output above")
    print("🐳 ECS Cluster: Check output above")
    print("⚖️  Load Balancer: Check output above")
    print("🌐 VPC/Subnets: Check output above")
    print("🗄️  DynamoDB: Check output above")
    print()
    print("Next Steps:")
    print("1. If infrastructure exists → Build and deploy Docker image")
    print("2. If infrastructure missing → Create required resources first")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
