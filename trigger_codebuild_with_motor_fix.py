#!/usr/bin/env python3
"""
Trigger CodeBuild to rebuild and deploy Alert Whisperer backend with motor fix
"""
import boto3
import time
import sys

# Configuration
PROJECT_NAME = "alert-whisperer-backend"
REGION = "us-east-1"

def trigger_build():
    """Trigger a new CodeBuild build"""
    print("🚀 Triggering CodeBuild for Alert Whisperer Backend")
    print("=" * 60)
    
    client = boto3.client('codebuild', region_name=REGION)
    
    try:
        # Start build
        print(f"\n📦 Starting build for project: {PROJECT_NAME}")
        response = client.start_build(projectName=PROJECT_NAME)
        
        build_id = response['build']['id']
        build_number = response['build']['buildNumber']
        
        print(f"✅ Build triggered successfully!")
        print(f"   Build ID: {build_id}")
        print(f"   Build Number: {build_number}")
        print(f"\n🔗 View in AWS Console:")
        print(f"   https://{REGION}.console.aws.amazon.com/codesuite/codebuild/projects/{PROJECT_NAME}/build/{build_id}")
        
        # Monitor build status
        print(f"\n⏳ Monitoring build status...")
        print("   (Press Ctrl+C to stop monitoring, build will continue)\n")
        
        previous_phase = None
        
        while True:
            build_info = client.batch_get_builds(ids=[build_id])['builds'][0]
            current_phase = build_info.get('currentPhase', 'UNKNOWN')
            build_status = build_info.get('buildStatus', 'UNKNOWN')
            
            # Print phase changes
            if current_phase != previous_phase:
                print(f"   📍 Phase: {current_phase} - Status: {build_status}")
                previous_phase = current_phase
            
            # Check if build completed
            if build_status in ['SUCCEEDED', 'FAILED', 'STOPPED', 'FAULT', 'TIMED_OUT']:
                print(f"\n{'✅' if build_status == 'SUCCEEDED' else '❌'} Build {build_status}")
                
                if build_status == 'SUCCEEDED':
                    print("\n🎉 Build successful! ECS will now deploy the new image...")
                    print("\n📊 Check ECS deployment:")
                    print("   aws ecs describe-services --cluster alert-whisperer-cluster --services alert-whisperer-backend-svc --region us-east-1")
                    print("\n📝 View ECS logs:")
                    print("   aws logs tail /ecs/alert-whisperer-backend --follow --region us-east-1")
                    print("\n🔍 Test backend health:")
                    print("   curl http://alertw-alb-1475356777.us-east-1.elb.amazonaws.com/api/health")
                    return 0
                else:
                    print(f"\n❌ Build failed with status: {build_status}")
                    print("\n📝 View build logs:")
                    print(f"   aws logs tail /aws/codebuild/{PROJECT_NAME} --follow --region {REGION}")
                    return 1
            
            time.sleep(5)
            
    except KeyboardInterrupt:
        print("\n\n⏸️  Monitoring stopped (build continues in background)")
        print(f"\n📊 Check build status:")
        print(f"   aws codebuild batch-get-builds --ids {build_id} --region {REGION}")
        return 0
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(trigger_build())
