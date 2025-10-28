import boto3
import os
from dotenv import load_dotenv

load_dotenv()

AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_SESSION_TOKEN = os.environ.get('AWS_SESSION_TOKEN')
TABLE_PREFIX = os.environ.get('DYNAMODB_TABLE_PREFIX', 'AlertWhisperer')

client_params = {
    'region_name': AWS_REGION,
    'aws_access_key_id': AWS_ACCESS_KEY_ID,
    'aws_secret_access_key': AWS_SECRET_ACCESS_KEY
}
if AWS_SESSION_TOKEN:
    client_params['aws_session_token'] = AWS_SESSION_TOKEN

dynamodb = boto3.client('dynamodb', **client_params)

missing_tables = [
    'RefreshTokens', 'RateLimits', 'WebhookSecurity', 
    'CorrelationConfigs', 'Kpis', 'SystemAuditLogs'
]

for table in missing_tables:
    table_name = f"{TABLE_PREFIX}_{table}"
    try:
        dynamodb.create_table(
            TableName=table_name,
            KeySchema=[{'AttributeName': 'id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'id', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        print(f"✅ Created table: {table_name}")
    except Exception as e:
        if 'ResourceInUseException' in str(e):
            print(f"⚠️  Table already exists: {table_name}")
        else:
            print(f"❌ Error creating {table_name}: {e}")

print("\n✅ All missing tables created!")
