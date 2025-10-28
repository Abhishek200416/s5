"""
Deploy Alert Whisperer backend using AWS CodeBuild
Uploads code to S3 and triggers build
"""
import boto3
import os
import zipfile
import time
from pathlib import Path

# AWS Configuration
AWS_REGION = 'us-east-1'
AWS_ACCOUNT_ID = '728925775278'
S3_BUCKET = 'alert-whisperer-deployments'
CODEBUILD_PROJECT = 'alert-whisperer-backend-build'
ECR_REPOSITORY = 'alert-whisperer-backend'

# Set AWS credentials from environment
os.environ['AWS_DEFAULT_REGION'] = AWS_REGION

def create_source_zip():
    """Create a zip file of the backend source code"""
    print("📦 Creating source code zip...")
    
    backend_dir = Path("/app/backend")
    zip_path = Path("/tmp/backend-source.zip")
    
    # Files to include
    files_to_include = [
        "*.py",
        "requirements.txt",
        "buildspec.yml",
        "Dockerfile.production"
    ]
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for pattern in files_to_include:
            for file_path in backend_dir.glob(pattern):
                if file_path.is_file():
                    arcname = file_path.name
                    zipf.write(file_path, arcname)
                    print(f"  ✅ Added: {arcname}")
    
    print(f"✅ Source zip created: {zip_path}")
    print(f"   Size: {zip_path.stat().st_size / 1024:.2f} KB")
    return zip_path

def upload_to_s3(zip_path, s3_client):
    """Upload source zip to S3"""
    print(f"\n📤 Uploading to S3 bucket: {S3_BUCKET}...")
    
    # Create bucket if it doesn't exist
    try:
        s3_client.head_bucket(Bucket=S3_BUCKET)
        print(f"✅ Bucket {S3_BUCKET} exists")
    except:
        print(f"⚠️  Creating bucket {S3_BUCKET}...")
        s3_client.create_bucket(Bucket=S3_BUCKET)
        print(f"✅ Bucket created")
    
    # Upload file
    s3_key = f"builds/backend-{int(time.time())}.zip"
    with open(zip_path, 'rb') as f:
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=s3_key,
            Body=f,
            ContentType='application/zip'
        )
    
    print(f"✅ Uploaded to s3://{S3_BUCKET}/{s3_key}")
    return s3_key

def trigger_codebuild(s3_key, codebuild_client):
    """Trigger CodeBuild project"""
    print(f"\n🚀 Triggering CodeBuild project: {CODEBUILD_PROJECT}...")
    
    response = codebuild_client.start_build(
        projectName=CODEBUILD_PROJECT,
        sourceLocationOverride=f"{S3_BUCKET}/{s3_key}",
        environmentVariablesOverride=[
            {
                'name': 'AWS_ACCOUNT_ID',
                'value': AWS_ACCOUNT_ID,
                'type': 'PLAINTEXT'
            },
            {
                'name': 'AWS_DEFAULT_REGION',
                'value': AWS_REGION,
                'type': 'PLAINTEXT'
            },
            {
                'name': 'IMAGE_REPO_NAME',
                'value': ECR_REPOSITORY,
                'type': 'PLAINTEXT'
            }
        ]
    )
    
    build_id = response['build']['id']
    build_arn = response['build']['arn']
    
    print(f"✅ Build started!")
    print(f"   Build ID: {build_id}")
    print(f"   Build ARN: {build_arn}")
    
    return build_id

def monitor_build(build_id, codebuild_client):
    """Monitor CodeBuild progress"""
    print(f"\n⏳ Monitoring build progress...")
    
    last_phase = None
    
    while True:
        response = codebuild_client.batch_get_builds(ids=[build_id])
        build = response['builds'][0]
        
        status = build['buildStatus']
        current_phase = build.get('currentPhase', 'STARTING')
        
        if current_phase != last_phase:
            print(f"   Phase: {current_phase}")
            last_phase = current_phase
        
        if status == 'SUCCEEDED':
            print(f"\n✅ Build SUCCEEDED!")
            print(f"   Duration: {build.get('phases', [{}])[-1].get('durationInSeconds', 0)}s")
            return True
        elif status in ['FAILED', 'STOPPED', 'FAULT', 'TIMED_OUT']:
            print(f"\n❌ Build {status}!")
            
            # Print failure details
            if 'phases' in build:
                for phase in build['phases']:
                    if phase.get('phaseStatus') == 'FAILED':
                        print(f"   Failed phase: {phase.get('phaseType')}")
                        if 'contexts' in phase:
                            for context in phase['contexts']:
                                print(f"   Error: {context.get('message')}")
            
            return False
        
        time.sleep(10)  # Check every 10 seconds

def update_ecs_service(ecs_client):
    """Force ECS service to use new task definition"""
    print(f"\n🔄 Updating ECS service...")
    
    cluster_name = 'alert-whisperer-cluster'
    service_name = 'alert-whisperer-backend-svc'
    
    try:
        response = ecs_client.update_service(
            cluster=cluster_name,
            service=service_name,
            forceNewDeployment=True
        )
        
        print(f"✅ ECS service updated!")
        print(f"   Service: {service_name}")
        print(f"   Cluster: {cluster_name}")
        print(f"   Deployment started")
        
        return True
    except Exception as e:
        print(f"⚠️  ECS update error: {e}")
        return False

def main():
    """Main deployment function"""
    print("=" * 60)
    print("🚀 Alert Whisperer Backend Deployment")
    print("=" * 60)
    
    # Initialize AWS clients
    s3_client = boto3.client('s3', region_name=AWS_REGION)
    codebuild_client = boto3.client('codebuild', region_name=AWS_REGION)
    ecs_client = boto3.client('ecs', region_name=AWS_REGION)
    
    try:
        # Step 1: Create source zip
        zip_path = create_source_zip()
        
        # Step 2: Upload to S3
        s3_key = upload_to_s3(zip_path, s3_client)
        
        # Step 3: Trigger CodeBuild
        build_id = trigger_codebuild(s3_key, codebuild_client)
        
        # Step 4: Monitor build
        success = monitor_build(build_id, codebuild_client)
        
        if success:
            # Step 5: Update ECS service
            update_ecs_service(ecs_client)
            
            print("\n" + "=" * 60)
            print("✅ DEPLOYMENT SUCCESSFUL!")
            print("=" * 60)
            print(f"\n🌐 Your backend is being deployed to ECS")
            print(f"   It will be live in approximately 30-60 seconds")
            print(f"\n📊 Monitor deployment:")
            print(f"   CloudWatch: https://console.aws.amazon.com/cloudwatch/home?region={AWS_REGION}")
            print(f"   ECS Service: https://console.aws.amazon.com/ecs/home?region={AWS_REGION}#/clusters/alert-whisperer-cluster/services/alert-whisperer-backend-svc")
            
        else:
            print("\n" + "=" * 60)
            print("❌ DEPLOYMENT FAILED!")
            print("=" * 60)
            print(f"\n🔍 Check CodeBuild logs:")
            print(f"   https://console.aws.amazon.com/codesuite/codebuild/projects/alert-whisperer-backend-build/history")
            
    except Exception as e:
        print(f"\n❌ Deployment error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
