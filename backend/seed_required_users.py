"""
Phase 1C: Seed DynamoDB with Required Users Only
- Admin: admin@alertwhisperer.com / admin123
- Tech: tech@acme.com / tech123  
- Company users for Acme Corporation
"""
import boto3
import os
import sys
from datetime import datetime, timezone
import uuid
import bcrypt
import secrets
from decimal import Decimal

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

dynamodb = boto3.resource('dynamodb', **dynamodb_params)

def generate_api_key():
    """Generate a secure API key"""
    return f"aw_{secrets.token_urlsafe(32)}"

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def seed_companies():
    """Create companies - keeping existing ones"""
    print("\n🏢 Seeding Companies...")
    companies_table = dynamodb.Table(f'{TABLE_PREFIX}Companies')
    
    companies = [
        {
            'id': 'comp-global',
            'name': 'Global Systems',
            'api_key': generate_api_key(),
            'policy': {
                'auto_approve_low_risk': True,
                'maintenance_window': 'Sat 22:00-02:00'
            },
            'assets': [],
            'critical_assets': [],
            'created_at': datetime.now(timezone.utc).isoformat()
        },
        {
            'id': 'comp-acme',
            'name': 'Acme Corporation',
            'api_key': generate_api_key(),
            'policy': {
                'auto_approve_low_risk': True,
                'maintenance_window': 'Sun 01:00-05:00'
            },
            'assets': [],
            'critical_assets': [],
            'created_at': datetime.now(timezone.utc).isoformat()
        }
    ]
    
    for company in companies:
        companies_table.put_item(Item=company)
        print(f"  ✅ Created company: {company['name']}")
        print(f"     API Key: {company['api_key']}")
    
    return companies

def seed_users():
    """Create ONLY required users - NO MSP admin"""
    print("\n👥 Seeding Users...")
    users_table = dynamodb.Table(f'{TABLE_PREFIX}Users')
    
    users = [
        {
            'id': str(uuid.uuid4()),
            'email': 'admin@alertwhisperer.com',
            'name': 'Admin User',
            'hashed_password': hash_password('admin123'),
            'password_hash': hash_password('admin123'),  # Support both field names
            'role': 'admin',  # Changed from msp_admin to admin
            'permissions': ['*'],
            'company_ids': ['comp-global'],
            'category': None,
            'created_at': datetime.now(timezone.utc).isoformat()
        },
        {
            'id': str(uuid.uuid4()),
            'email': 'tech@acme.com',
            'name': 'Tech Support',
            'hashed_password': hash_password('tech123'),
            'password_hash': hash_password('tech123'),  # Support both field names
            'role': 'technician',
            'permissions': ['view_alerts', 'manage_assigned_incidents', 'execute_runbooks'],
            'company_ids': ['comp-acme'],
            'category': 'Server',  # Added category as requested
            'created_at': datetime.now(timezone.utc).isoformat()
        },
        {
            'id': str(uuid.uuid4()),
            'email': 'company@acme.com',
            'name': 'Company Admin',
            'hashed_password': hash_password('company123'),
            'password_hash': hash_password('company123'),
            'role': 'company_admin',
            'permissions': ['view_alerts', 'manage_incidents', 'view_reports', 'manage_technicians'],
            'company_ids': ['comp-acme'],
            'category': None,
            'created_at': datetime.now(timezone.utc).isoformat()
        }
    ]
    
    for user in users:
        users_table.put_item(Item=user)
        print(f"  ✅ Created user: {user['email']} ({user['role']})")
        if user.get('category'):
            print(f"     Category: {user['category']}")
    
    return users

def seed_kpis(companies):
    """Create KPI tracking for each company"""
    print("\n📊 Seeding KPIs...")
    kpis_table = dynamodb.Table(f'{TABLE_PREFIX}Kpis')
    
    for company in companies:
        kpi = {
            'id': str(uuid.uuid4()),
            'company_id': company['id'],
            'total_alerts': 0,
            'total_incidents': 0,
            'noise_reduction_pct': Decimal('0.0'),
            'mttr_minutes': Decimal('0.0'),
            'self_healed_count': 0,
            'self_healed_pct': Decimal('0.0'),
            'patch_compliance_pct': Decimal('0.0'),
            'updated_at': datetime.now(timezone.utc).isoformat()
        }
        kpis_table.put_item(Item=kpi)
        print(f"  ✅ Created KPI for: {company['name']}")

def seed_correlation_configs(companies):
    """Create correlation configs for each company"""
    print("\n⚙️  Seeding Correlation Configs...")
    configs_table = dynamodb.Table(f'{TABLE_PREFIX}CorrelationConfigs')
    
    for company in companies:
        config = {
            'id': str(uuid.uuid4()),
            'company_id': company['id'],
            'time_window_minutes': 15,
            'aggregation_key': 'asset|signature',
            'auto_correlate': True,
            'min_alerts_for_incident': 1,
            'updated_at': datetime.now(timezone.utc).isoformat()
        }
        configs_table.put_item(Item=config)
        print(f"  ✅ Created correlation config for: {company['name']}")

def seed_runbooks():
    """Create sample runbooks for Acme"""
    print("\n📖 Seeding Runbooks...")
    runbooks_table = dynamodb.Table(f'{TABLE_PREFIX}Runbooks')
    
    runbooks = [
        {
            'id': str(uuid.uuid4()),
            'company_id': 'comp-acme',
            'name': 'Restart Web Server',
            'description': 'Restart nginx web server service',
            'risk_level': 'low',
            'signature': 'high_response_time',
            'actions': ['systemctl restart nginx', 'systemctl status nginx'],
            'health_checks': {'service_status': 'active'},
            'auto_approve': True
        },
        {
            'id': str(uuid.uuid4()),
            'company_id': 'comp-acme',
            'name': 'Clear Disk Space',
            'description': 'Clean up temporary files and logs',
            'risk_level': 'low',
            'signature': 'disk_space_critical',
            'actions': ['rm -rf /tmp/*', 'journalctl --vacuum-time=7d', 'df -h'],
            'health_checks': {'disk_usage': 'below_80'},
            'auto_approve': True
        },
        {
            'id': str(uuid.uuid4()),
            'company_id': 'comp-global',
            'name': 'Database Connection Reset',
            'description': 'Reset database connection pool',
            'risk_level': 'medium',
            'signature': 'database_connection_timeout',
            'actions': ['systemctl restart postgresql', 'pg_isready'],
            'health_checks': {'db_status': 'accepting connections'},
            'auto_approve': False
        }
    ]
    
    for runbook in runbooks:
        runbooks_table.put_item(Item=runbook)
        print(f"  ✅ Created runbook: {runbook['name']} ({runbook['risk_level']} risk)")

def main():
    print("\n" + "="*60)
    print("  🌱 SEED DYNAMODB - CREATE REQUIRED USERS ONLY")
    print("="*60)
    
    try:
        companies = seed_companies()
        users = seed_users()
        seed_kpis(companies)
        seed_correlation_configs(companies)
        seed_runbooks()
        
        print("\n" + "="*60)
        print("  ✅ SEED COMPLETE!")
        print("="*60)
        print("\n📝 Login Credentials:")
        print("  Admin: admin@alertwhisperer.com / admin123")
        print("  Tech: tech@acme.com / tech123")
        print("  Company Admin: company@acme.com / company123")
        print("\n📝 Companies:")
        for company in companies:
            print(f"  {company['name']}: {company['api_key']}")
        print("\n")
        
        return 0
    
    except Exception as e:
        print(f"\n❌ Seed failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
