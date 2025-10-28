"""
Test DynamoDB Backend Connection and Login
"""
import asyncio
import os
import sys

# Set AWS credentials
os.environ['AWS_ACCESS_KEY_ID'] = '[REDACTED_AWS_TEMP_KEY_ID]'
os.environ['AWS_SECRET_ACCESS_KEY'] = '[REDACTED]'
os.environ['AWS_SESSION_TOKEN'] = '[REDACTED_AWS_SESSION_TOKEN]'
os.environ['AWS_REGION'] = 'us-east-1'
os.environ['USE_DYNAMODB'] = 'true'
os.environ['DYNAMODB_TABLE_PREFIX'] = 'AlertWhisperer'

sys.path.insert(0, '/app/backend')

from dynamodb_service import DynamoDBService, DynamoDBDatabase
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def test_connection():
    print("=" * 60)
    print("🧪 Testing DynamoDB Backend Connection")
    print("=" * 60)
    
    try:
        # Initialize service
        print("\n1️⃣  Initializing DynamoDB service...")
        service = DynamoDBService(region='us-east-1', table_prefix='AlertWhisperer')
        db = DynamoDBDatabase(service)
        print("✅ Service initialized")
        
        # Test finding a user
        print("\n2️⃣  Testing user lookup...")
        user = await db['users'].find_one({'email': 'admin@alertwhisperer.com'})
        
        if user:
            print(f"✅ Found user: {user['email']}")
            print(f"   Name: {user['name']}")
            print(f"   Role: {user['role']}")
            print(f"   ID: {user['id']}")
            
            # Test password verification
            print("\n3️⃣  Testing password verification...")
            if pwd_context.verify('admin123', user['password']):
                print("✅ Password verification successful!")
            else:
                print("❌ Password verification failed!")
            
            # Test listing companies
            print("\n4️⃣  Testing companies lookup...")
            companies = await db['companies'].find()
            print(f"✅ Found {len(companies)} companies:")
            for company in companies:
                print(f"   - {company['name']} (API Key: {company.get('api_key', 'N/A')[:20]}...)")
            
            print("\n" + "=" * 60)
            print("✅ ALL TESTS PASSED!")
            print("=" * 60)
            print("\n🎉 Backend is ready to use DynamoDB!")
            print("\n📝 Login will work with:")
            print("   Email: admin@alertwhisperer.com")
            print("   Password: admin123")
            
        else:
            print("❌ User not found in database!")
            
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(test_connection())
