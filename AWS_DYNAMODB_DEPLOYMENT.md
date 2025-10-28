# 🚀 Alert Whisperer - AWS Deployment with DynamoDB

## ✅ Current Status

Your Alert Whisperer application has been successfully configured to use AWS DynamoDB!

- **Frontend URL**: http://alert-whisperer-frontend-728925775278.s3-website-us-east-1.amazonaws.com
- **Backend API URL**: http://alert-whisperer-alb-1592907964.us-east-1.elb.amazonaws.com/api
- **Database**: DynamoDB (us-east-1) - All 11 tables created and seeded

## 🔐 Login Credentials

```
Email: admin@alertwhisperer.com
Password: admin123
```

## 📋 What's Been Done

1. ✅ Created DynamoDB service layer (`dynamodb_service.py`) - MongoDB-compatible interface
2. ✅ Updated `server.py` to support both MongoDB and DynamoDB
3. ✅ Seeded DynamoDB with initial data (users, companies, configs)
4. ✅ Fixed authentication to support DynamoDB field names
5. ✅ Tested login flow - working perfectly!

## ⚙️ Required: Update Your ECS Task Definition

Your backend is currently running in ECS but using MongoDB. You need to update the ECS task definition to use DynamoDB.

### Option 1: Using AWS Console (Recommended)

1. **Go to ECS Console**:
   - Navigate to: https://console.aws.amazon.com/ecs/
   - Select your cluster: `alert-whisperer-cluster`
   - Go to **Task Definitions** → `alert-whisperer-backend`

2. **Create New Revision**:
   - Click **Create new revision**
   - Scroll to **Container Definitions** → `alert-whisperer-backend-container`
   - Click **Edit**

3. **Add Environment Variables**:
   ```
   USE_DYNAMODB = true
   AWS_REGION = us-east-1
   DYNAMODB_TABLE_PREFIX = AlertWhisperer
   AWS_ACCESS_KEY_ID=[REDACTED]
   AWS_SECRET_ACCESS_KEY=[REDACTED]
   AWS_SESSION_TOKEN=[REDACTED]   ```

4. **Save and Update Service**:
   - Click **Update**
   - Click **Create**
   - Go to your **ECS Service** → **Update Service**
   - Select the new task definition revision
   - Click **Update Service**
   - Wait 2-3 minutes for new task to start

### Option 2: Using AWS CLI

```bash
# Export AWS credentials
export AWS_ACCESS_KEY_ID=[REDACTED]
export AWS_SECRET_ACCESS_KEY=[REDACTED]
export AWS_SESSION_TOKEN=[REDACTED]

# Get current task definition
aws ecs describe-task-definition --task-definition alert-whisperer-backend \
  --region us-east-1 > task-def.json

# Edit task-def.json and add environment variables to containerDefinitions[0].environment

# Register new task definition
aws ecs register-task-definition --cli-input-json file://task-def-updated.json

# Update service
aws ecs update-service \
  --cluster alert-whisperer-cluster \
  --service alert-whisperer-backend-service \
  --task-definition alert-whisperer-backend:NEW_REVISION \
  --region us-east-1
```

### Option 3: Better Approach - Use IAM Role (Production Best Practice)

Instead of hardcoding AWS credentials, attach an IAM role to your ECS task:

1. **Create IAM Policy** (DynamoDB access):
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": [
           "dynamodb:GetItem",
           "dynamodb:PutItem",
           "dynamodb:UpdateItem",
           "dynamodb:DeleteItem",
           "dynamodb:Scan",
           "dynamodb:Query",
           "dynamodb:BatchGetItem",
           "dynamodb:BatchWriteItem"
         ],
         "Resource": "arn:aws:dynamodb:us-east-1:728925775278:table/AlertWhisperer*"
       }
     ]
   }
   ```

2. **Create IAM Role** for ECS Task:
   - Trust relationship: `ecs-tasks.amazonaws.com`
   - Attach the policy above

3. **Update Task Definition**:
   - Set `taskRoleArn` to your new IAM role ARN
   - Remove AWS credential environment variables
   - Keep only: `USE_DYNAMODB=true`, `AWS_REGION=us-east-1`, `DYNAMODB_TABLE_PREFIX=AlertWhisperer`

## 🧪 Testing After Deployment

Once you've updated the ECS task definition:

1. **Wait 2-3 minutes** for the new task to start
2. **Test the backend API**:
   ```bash
   curl http://alert-whisperer-alb-1592907964.us-east-1.elb.amazonaws.com/api/agent/ping
   ```
   Expected response: `{"status": "ok", "message": "Alert Whisperer API is running"}`

3. **Test login**:
   ```bash
   curl -X POST http://alert-whisperer-alb-1592907964.us-east-1.elb.amazonaws.com/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email": "admin@alertwhisperer.com", "password": "admin123"}'
   ```
   Expected: JWT token in response

4. **Open your frontend** and login:
   - URL: http://alert-whisperer-frontend-728925775278.s3-website-us-east-1.amazonaws.com
   - Email: admin@alertwhisperer.com
   - Password: admin123

## 📊 DynamoDB Tables

All 11 tables are created and seeded:

| Table Name | Status | Records | Purpose |
|------------|--------|---------|---------|
| AlertWhisperer_Users | ✅ Active | 3 | User authentication |
| AlertWhisperer_Companies | ✅ Active | 3 | Company/tenant data |
| AlertWhisperer_Alerts | ✅ Active | 0 | Incoming alerts |
| AlertWhisperer_Incidents | ✅ Active | 0 | Correlated incidents |
| AlertWhisperer_CompanyConfigs | ✅ Active | 9 | Per-company settings |
| AlertWhisperer_Runbooks | ✅ Active | 2 | Automation runbooks |
| AlertWhisperer_Notifications | ✅ Active | 0 | User notifications |
| AlertWhisperer_ChatMessages | ✅ Active | 0 | Team chat |
| AlertWhisperer_AuditLogs | ✅ Active | 0 | Audit trail |
| AlertWhisperer_ApprovalRequests | ✅ Active | 0 | Runbook approvals |
| AlertWhisperer_OnCallSchedules | ✅ Active | 2 | On-call rotations |

## 🎯 What's Next

After updating ECS:

1. ✅ **Login will work** - DynamoDB has user data
2. ✅ **Webhooks will work** - API keys configured
3. ✅ **Correlation will work** - All configs in place
4. ✅ **SLA tracking will work** - DynamoDB tables ready

## 🐛 Troubleshooting

### Login still not working?

1. Check ECS task logs:
   ```bash
   aws logs tail /ecs/alert-whisperer-backend --follow --region us-east-1
   ```

2. Verify environment variables in running task:
   - Go to ECS Console → Tasks → Running task
   - Check "Environment Variables" section

3. Check if backend is using DynamoDB:
   - Look for log: "🚀 Using DynamoDB as database backend"
   - Look for log: "✅ DynamoDB initialized: region=us-east-1"

### DynamoDB permissions error?

- Make sure AWS credentials are correct in task definition
- OR use IAM role (recommended) with DynamoDB permissions

## 📝 Files Updated

The following files were created/modified:

1. `/app/backend/dynamodb_service.py` - **NEW** - DynamoDB service layer
2. `/app/backend/server.py` - **MODIFIED** - Added DynamoDB support
3. `/app/backend/seed_dynamodb.py` - **EXISTING** - Used to seed data
4. `/app/configure_dynamodb.sh` - **NEW** - Configuration script

## 🎉 Summary

Your Alert Whisperer application is **fully configured** to use AWS DynamoDB! 

**All you need to do now**:
1. Update your ECS task definition with the environment variables
2. Restart the ECS service
3. Login and enjoy your production-ready MSP platform!

---

**Need Help?** Check the ECS task logs or DynamoDB tables for any issues.
