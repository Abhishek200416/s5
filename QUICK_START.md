# 🚀 Quick Start: Deploy Alert Whisperer to AWS

## ✅ What's Already Done

Your AWS infrastructure is **100% READY**:
- ✅ ECR Repository created
- ✅ ECS Cluster running
- ✅ Load Balancer configured
- ✅ DynamoDB tables set up (11 tables)
- ✅ VPC & Security Groups configured
- ✅ AWS credentials validated

**All you need to do: Build & Deploy the Docker image!**

---

## 🎯 Deploy in 3 Simple Steps

### Prerequisites:
- Docker installed on your computer ([Get Docker](https://docs.docker.com/get-docker/))
- AWS CLI installed ([Get AWS CLI](https://aws.amazon.com/cli/))
- Project files downloaded to your computer

---

### Step 1: Get Fresh AWS Credentials (Important!)

Your temporary credentials expire after a few hours. Get fresh ones:

1. Go to: https://superopsglobalhackathon.awsapps.com/start
2. Login with: `abhishekollurii@gmail.com` / `Wq@VW3gksX89_0d`
3. Click on your AWS account
4. Click **"Command line or programmatic access"**
5. Copy and run the `export` commands in your terminal

Example:
```bash
export AWS_REGION=us-east-1
export AWS_ACCESS_KEY_ID=[REDACTED]
export AWS_SECRET_ACCESS_KEY=[REDACTED]
export AWS_SESSION_TOKEN=[REDACTED]
```

Test credentials work:
```bash
aws sts get-caller-identity
```

---

### Step 2: Run the Deployment Script

```bash
# Navigate to project directory
cd /path/to/alert-whisperer

# Run deployment
./deploy_complete.sh
```

**That's it!** The script will:
1. ✅ Register task definition
2. ✅ Login to ECR
3. ✅ Build Docker image
4. ✅ Push to ECR
5. ✅ Create/Update ECS service
6. ✅ Wait for deployment
7. ✅ Test backend

**Time: 5-10 minutes** (depending on internet speed)

---

### Step 3: Verify Deployment

Test the backend:
```bash
curl http://alert-whisperer-alb-1592907964.us-east-1.elb.amazonaws.com/api/companies
```

Should return JSON with companies list! 🎉

---

## 🌐 Your Deployment URLs

**Backend API:**  
`http://alert-whisperer-alb-1592907964.us-east-1.elb.amazonaws.com/api`

**Test Endpoints:**
- Companies: `/api/companies`
- Health Check: `/api/companies` (200 = healthy)
- Login: `/api/auth/login` (POST)

---

## 📱 Update Frontend (After Backend Deployed)

1. Edit `frontend/.env`:
```bash
REACT_APP_BACKEND_URL=http://alert-whisperer-alb-1592907964.us-east-1.elb.amazonaws.com/api
```

2. Rebuild frontend:
```bash
cd frontend
yarn install
yarn build
```

3. Deploy to S3 (if using S3 for frontend):
```bash
aws s3 sync build/ s3://your-frontend-bucket/
```

---

## 🐛 Common Issues & Solutions

### ❌ "AWS credentials not configured"
**Solution:** Get fresh credentials from SSO portal (they expire!)

### ❌ "Docker command not found"
**Solution:** Install Docker: https://docs.docker.com/get-docker/

### ❌ "aws command not found"
**Solution:** Install AWS CLI: https://aws.amazon.com/cli/

### ❌ Backend returns 502 Bad Gateway
**Solution:** 
1. Service might still be starting (wait 2-3 minutes)
2. Check logs: `aws logs tail /ecs/alert-whisperer-backend --follow`
3. Verify task is running: `aws ecs list-tasks --cluster alert-whisperer-cluster`

### ❌ "Permission denied" when running script
**Solution:** Make executable: `chmod +x deploy_complete.sh`

---

## 📊 Monitor Your Deployment

### View CloudWatch Logs:
```bash
aws logs tail /ecs/alert-whisperer-backend --follow
```

### Check Service Status:
```bash
aws ecs describe-services \
    --cluster alert-whisperer-cluster \
    --services alert-whisperer-backend-service \
    --query 'services[0].{Status:status,Running:runningCount}'
```

### Check Target Health:
```bash
aws elbv2 describe-target-health \
    --target-group-arn arn:aws:elasticloadbalancing:us-east-1:728925775278:targetgroup/alert-whisperer-tg/45498287296a370f
```

---

## 🔄 Redeploy (After Code Changes)

To deploy code changes:

```bash
# 1. Make your code changes
# 2. Run deployment script again
./deploy_complete.sh

# OR manually force new deployment:
aws ecs update-service \
    --cluster alert-whisperer-cluster \
    --service alert-whisperer-backend-service \
    --force-new-deployment
```

---

## 📁 Project Files Reference

**Deployment Files:**
- `deploy_complete.sh` - Main deployment script (USE THIS)
- `deploy_to_aws.sh` - Alternative deployment script
- `backend/Dockerfile.production` - Production Docker configuration
- `backend/task-definition.json` - ECS task configuration
- `backend/.env` - Environment variables (AWS credentials)

**Helper Scripts:**
- `check_aws_infrastructure.py` - Check infrastructure status
- `check_deployment_status.py` - Check service status
- `backend/check_aws_infrastructure.py` - Backend infrastructure check

**Documentation:**
- `AWS_DEPLOYMENT_GUIDE.md` - Detailed deployment guide
- `QUICK_START.md` - This file

---

## 💰 Cost Estimate

**Monthly AWS Costs (approximate):**
- ECS Fargate (1 task): ~$15-20
- DynamoDB (on-demand): ~$2-5
- Application Load Balancer: ~$16
- Data Transfer: ~$5
- CloudWatch Logs: ~$2
- **Total: ~$40-50/month**

To minimize costs:
- Stop ECS service when not in use
- Use DynamoDB on-demand pricing
- Monitor usage in AWS Cost Explorer

---

## ✅ Success Checklist

After deployment, verify:

- [ ] Backend API returns 200 status
- [ ] Can login: `POST /api/auth/login`
- [ ] Can get companies: `GET /api/companies`
- [ ] ECS task is running (1/1)
- [ ] Load balancer health checks pass
- [ ] CloudWatch logs show no errors
- [ ] Frontend can connect to backend

---

## 🆘 Need Help?

1. **Check logs:**
   ```bash
   aws logs tail /ecs/alert-whisperer-backend --follow
   ```

2. **Check detailed guide:**
   Open `AWS_DEPLOYMENT_GUIDE.md` for step-by-step instructions

3. **Verify infrastructure:**
   ```bash
   python3 check_aws_infrastructure.py
   ```

4. **Check service status:**
   ```bash
   python3 check_deployment_status.py
   ```

---

## 🎉 You're Ready!

Your Alert Whisperer MSP platform is production-ready on AWS!

**Features:**
- ✅ Real-time alert monitoring
- ✅ AI-powered correlation
- ✅ Auto-remediation with runbooks
- ✅ SLA management & escalation
- ✅ Multi-tenant MSP support
- ✅ RBAC & audit logging
- ✅ Webhook integrations
- ✅ DynamoDB NoSQL database
- ✅ Scalable ECS Fargate deployment

**Next Steps:**
1. Deploy backend ✅
2. Update frontend .env
3. Test all features
4. Configure your MSP companies
5. Set up webhook integrations
6. Monitor via CloudWatch

---

**Happy Deploying! 🚀**
