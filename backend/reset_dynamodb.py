"""
Phase 1: Reset DynamoDB - Delete and Recreate All Tables
"""
import boto3
import os
import sys
from botocore.exceptions import ClientError
import time

# AWS Configuration
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_SESSION_TOKEN = os.environ.get('AWS_SESSION_TOKEN')
TABLE_PREFIX = 'AlertWhisperer_'

# Initialize DynamoDB
dynamodb_params = {
    'region_name': AWS_REGION,
    'aws_access_key_id': AWS_ACCESS_KEY_ID,
    'aws_secret_access_key': AWS_SECRET_ACCESS_KEY
}
if AWS_SESSION_TOKEN:
    dynamodb_params['aws_session_token'] = AWS_SESSION_TOKEN

dynamodb = boto3.client('dynamodb', **dynamodb_params)
dynamodb_resource = boto3.resource('dynamodb', **dynamodb_params)

# All table names
TABLE_NAMES = [
    'Users', 'Companies', 'CompanyConfigs', 'Alerts', 'Incidents',
    'Runbooks', 'Kpis', 'ChatMessages', 'Notifications', 'AuditLogs',
    'ApprovalRequests', 'RateLimits', 'RefreshTokens', 'SystemAuditLogs',
    'OnCallSchedules', 'WebhookSecurity', 'CorrelationConfigs', 'PatchCompliance'
]

def delete_all_tables():
    """Delete all AlertWhisperer DynamoDB tables"""
    print("\n🗑️  PHASE 1A: Deleting ALL DynamoDB Tables...")
    print("="*60)
    
    deleted_count = 0
    for table_name in TABLE_NAMES:
        full_table_name = f"{TABLE_PREFIX}{table_name}"
        try:
            table = dynamodb_resource.Table(full_table_name)
            table.delete()
            print(f"  ✅ Deleted: {full_table_name}")
            deleted_count += 1
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                print(f"  ⚠️  Table not found (skipping): {full_table_name}")
            else:
                print(f"  ❌ Error deleting {full_table_name}: {e}")
    
    if deleted_count > 0:
        print(f"\n⏳ Waiting for {deleted_count} tables to be deleted...")
        time.sleep(10)  # Wait for deletion to complete
    
    print(f"\n✅ Deleted {deleted_count} tables")
    return deleted_count

def create_table(table_name, key_schema, attribute_definitions, gsi_list=None):
    """Create a DynamoDB table"""
    full_table_name = f"{TABLE_PREFIX}{table_name}"
    
    try:
        params = {
            'TableName': full_table_name,
            'KeySchema': key_schema,
            'AttributeDefinitions': attribute_definitions,
            'BillingMode': 'PAY_PER_REQUEST'
        }
        
        if gsi_list:
            params['GlobalSecondaryIndexes'] = gsi_list
        
        dynamodb.create_table(**params)
        print(f"  ✅ Created: {full_table_name}")
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print(f"  ⚠️  Table already exists: {full_table_name}")
        else:
            print(f"  ❌ Error creating {full_table_name}: {e}")
        return False

def create_all_tables():
    """Create all AlertWhisperer DynamoDB tables"""
    print("\n📦 PHASE 1B: Creating ALL DynamoDB Tables...")
    print("="*60)
    
    created_count = 0
    
    # Users Table - with email GSI
    if create_table(
        'Users',
        [{'AttributeName': 'id', 'KeyType': 'HASH'}],
        [
            {'AttributeName': 'id', 'AttributeType': 'S'},
            {'AttributeName': 'email', 'AttributeType': 'S'}
        ],
        [{
            'IndexName': 'email-index',
            'KeySchema': [{'AttributeName': 'email', 'KeyType': 'HASH'}],
            'Projection': {'ProjectionType': 'ALL'}
        }]
    ):
        created_count += 1
    
    # Companies Table - with name GSI
    if create_table(
        'Companies',
        [{'AttributeName': 'id', 'KeyType': 'HASH'}],
        [
            {'AttributeName': 'id', 'AttributeType': 'S'},
            {'AttributeName': 'name', 'AttributeType': 'S'}
        ],
        [{
            'IndexName': 'name-index',
            'KeySchema': [{'AttributeName': 'name', 'KeyType': 'HASH'}],
            'Projection': {'ProjectionType': 'ALL'}
        }]
    ):
        created_count += 1
    
    # CompanyConfigs Table
    if create_table(
        'CompanyConfigs',
        [{'AttributeName': 'id', 'KeyType': 'HASH'}],
        [{'AttributeName': 'id', 'AttributeType': 'S'}]
    ):
        created_count += 1
    
    # Alerts Table - with company_id GSI
    if create_table(
        'Alerts',
        [{'AttributeName': 'id', 'KeyType': 'HASH'}],
        [
            {'AttributeName': 'id', 'AttributeType': 'S'},
            {'AttributeName': 'company_id', 'AttributeType': 'S'}
        ],
        [{
            'IndexName': 'company_id-index',
            'KeySchema': [{'AttributeName': 'company_id', 'KeyType': 'HASH'}],
            'Projection': {'ProjectionType': 'ALL'}
        }]
    ):
        created_count += 1
    
    # Incidents Table - with company_id GSI
    if create_table(
        'Incidents',
        [{'AttributeName': 'id', 'KeyType': 'HASH'}],
        [
            {'AttributeName': 'id', 'AttributeType': 'S'},
            {'AttributeName': 'company_id', 'AttributeType': 'S'}
        ],
        [{
            'IndexName': 'company_id-index',
            'KeySchema': [{'AttributeName': 'company_id', 'KeyType': 'HASH'}],
            'Projection': {'ProjectionType': 'ALL'}
        }]
    ):
        created_count += 1
    
    # Runbooks Table - with company_id GSI
    if create_table(
        'Runbooks',
        [{'AttributeName': 'id', 'KeyType': 'HASH'}],
        [
            {'AttributeName': 'id', 'AttributeType': 'S'},
            {'AttributeName': 'company_id', 'AttributeType': 'S'}
        ],
        [{
            'IndexName': 'company_id-index',
            'KeySchema': [{'AttributeName': 'company_id', 'KeyType': 'HASH'}],
            'Projection': {'ProjectionType': 'ALL'}
        }]
    ):
        created_count += 1
    
    # Simple tables (no GSI)
    simple_tables = [
        'Kpis', 'ChatMessages', 'Notifications', 'AuditLogs',
        'ApprovalRequests', 'RateLimits', 'RefreshTokens', 
        'SystemAuditLogs', 'OnCallSchedules', 'WebhookSecurity',
        'CorrelationConfigs', 'PatchCompliance'
    ]
    
    for table_name in simple_tables:
        if create_table(
            table_name,
            [{'AttributeName': 'id', 'KeyType': 'HASH'}],
            [{'AttributeName': 'id', 'AttributeType': 'S'}]
        ):
            created_count += 1
    
    if created_count > 0:
        print(f"\n⏳ Waiting for {created_count} tables to become active...")
        time.sleep(15)  # Wait for tables to become active
    
    print(f"\n✅ Created {created_count} tables")
    return created_count

def main():
    print("\n" + "="*60)
    print("  🚀 DYNAMODB RESET - DELETE & RECREATE ALL TABLES")
    print("="*60)
    
    try:
        # Phase 1A: Delete all tables
        deleted = delete_all_tables()
        
        # Phase 1B: Create all tables
        created = create_all_tables()
        
        print("\n" + "="*60)
        print(f"  ✅ RESET COMPLETE!")
        print(f"     Deleted: {deleted} tables")
        print(f"     Created: {created} tables")
        print("="*60)
        
        return 0
    
    except Exception as e:
        print(f"\n❌ Reset failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
