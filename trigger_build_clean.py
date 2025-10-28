#!/usr/bin/env python3
"""Trigger CodeBuild without credentials"""

import boto3
import os

# Set AWS credentials from environment
os.environ['AWS_ACCESS_KEY_ID'] = os.getenv('AWS_KEY_ID', '')
os.environ['AWS_SECRET_ACCESS_KEY'] = os.getenv('AWS_SECRET', '')
os.environ['AWS_SESSION_TOKEN'] = os.getenv('AWS_TOKEN', '')
os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'

client = boto3.client('codebuild', region_name='us-east-1')

try:
    response = client.start_build(projectName='alert-whisperer-backend-build')
    print(f"✅ Build triggered: {response['build']['id']}")
    print("⏳ Wait 3-5 minutes for build to complete")
    print("📊 Monitor: https://console.aws.amazon.com/codesuite/codebuild/projects/alert-whisperer-backend-build/history")
except Exception as e:
    print(f"❌ Error: {e}")
