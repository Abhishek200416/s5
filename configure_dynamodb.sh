#!/bin/bash

# Alert Whisperer - AWS DynamoDB Deployment Script
# This script configures and tests the backend with DynamoDB

echo "=" 
echo "🚀 Alert Whisperer - DynamoDB Configuration"
echo "="

# Set AWS credentials from user's session
export AWS_ACCESS_KEY_ID=[REDACTED]
export AWS_SECRET_ACCESS_KEY=[REDACTED]
export AWS_SESSION_TOKEN=[REDACTED]
export AWS_REGION="us-east-1"
export USE_DYNAMODB="true"
export DYNAMODB_TABLE_PREFIX="AlertWhisperer"

echo ""
echo "✅ AWS credentials configured"
echo "📍 Region: us-east-1"
echo "📦 Table Prefix: AlertWhisperer"
echo ""

# Test DynamoDB connection
echo "🔍 Testing DynamoDB connection..."
python3 << 'EOF'
import boto3
import os

try:
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    
    # List tables
    tables = list(dynamodb.tables.all())
    print(f"✅ Connected to DynamoDB successfully!")
    print(f"📋 Found {len(tables)} tables:")
    for table in tables:
        if 'AlertWhisperer' in table.name:
            print(f"   - {table.name}")
    print("")
except Exception as e:
    print(f"❌ Failed to connect to DynamoDB: {e}")
    exit(1)
EOF

if [ $? -ne 0 ]; then
    echo "❌ DynamoDB connection test failed"
    exit 1
fi

# Seed DynamoDB (if needed)
echo "🌱 Seeding DynamoDB with initial data..."
cd /app/backend
python3 seed_dynamodb.py

echo ""
echo "=" 
echo "✅ Configuration Complete!"
echo "="
echo ""
echo "🔐 Demo Credentials:"
echo "   Email: admin@alertwhisperer.com"
echo "   Password: admin123"
echo ""
echo "🌐 Your Deployment:"
echo "   Frontend: http://alert-whisperer-frontend-728925775278.s3-website-us-east-1.amazonaws.com"
echo "   Backend API: http://alert-whisperer-alb-1592907964.us-east-1.elb.amazonaws.com/api"
echo ""
echo "⚠️  IMPORTANT: You need to configure these environment variables in your ECS task definition:"
echo "   - USE_DYNAMODB=true"
echo "   - AWS_REGION=us-east-1"
echo "   - DYNAMODB_TABLE_PREFIX=AlertWhisperer"
echo "   - AWS_ACCESS_KEY_ID=[REDACTED]
echo "   - AWS_SECRET_ACCESS_KEY=[REDACTED] secret key)"
echo "   - AWS_SESSION_TOKEN=[REDACTED] session token)"
echo ""
