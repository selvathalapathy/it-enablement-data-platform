# 🚨 Incident Response Runbook — IT Enablement Platform

## Simple Explanation (like you're in school)
A runbook is like a **fire drill procedure** posted on the school wall.
When an emergency happens, everyone follows the same steps calmly
instead of panicking. This runbook tells you exactly what to do
when something goes wrong with the IT Enablement platform.

---

## Incident Severity Levels

| Level | Name | Example | Response Time |
|-------|------|---------|--------------|
| P1 | Critical | ETL completely down, no data flowing | 15 minutes |
| P2 | High | ETL delayed by >2 hours | 1 hour |
| P3 | Medium | Single report missing data | 4 hours |
| P4 | Low | Minor dashboard formatting issue | Next business day |

---

## Step 1: DETECT — How We Know Something Is Wrong

**Automatic alerts (CloudWatch will notify you):**
- Email to: selvathalapathy@gmail.com
- Subject: `[ALARM] IT-Enablement-Platform - ETL-Pipeline-Failed`

**Manual checks:**
- Power BI dashboard shows stale data (timestamp not today's date)
- Business users report missing reports
- CloudWatch dashboard shows red alarms

---

## Step 2: ASSESS — How Bad Is It?

When you get an alert, ask these questions:

```
1. Is the ETL completely stopped? → P1
2. Is data delayed but will recover? → P2
3. Is only one report affected? → P3
4. Is it just a visual issue? → P4
```

---

## Step 3: COMMUNICATE — Tell The Team

**For P1/P2 incidents, immediately notify:**
1. Your manager
2. Business stakeholders (they need to know reports will be late)
3. Update the incident log (see template below)

**Communication template:**
```
Subject: [P1 INCIDENT] IT Enablement ETL Pipeline - <date>

Status: INVESTIGATING
Issue: ETL pipeline has not completed as of <time>
Impact: Daily transaction reports for <date> are not yet available
Next Update: In 30 minutes

Engineer: Selvathalapathy
```

---

## Step 4: INVESTIGATE — Find The Problem

### Check 1: Is the ETL job running?
```bash
# Check CloudWatch logs for ETL pipeline
aws logs filter-log-events \
  --log-group-name "/it-enablement/prod/etl-pipeline" \
  --start-time $(date -d '2 hours ago' +%s000) \
  --filter-pattern "ERROR"
```

### Check 2: Is S3 data available?
```bash
# Check if raw data landed in S3 today
aws s3 ls s3://it-enablement-prod-data-lake/raw/transactions/$(date +%Y-%m-%d)/
```

### Check 3: Is the API reachable?
```bash
# Test API connectivity
curl -I https://api.example-payments.com/v1/health
# Expected: HTTP 200 OK
```

### Check 4: Check CloudWatch metrics
```bash
# Get ETL success metric for last 24 hours
aws cloudwatch get-metric-statistics \
  --namespace "ITEnablement/ETL" \
  --metric-name "ETLSuccess" \
  --dimensions Name=Pipeline,Value=TransactionETL \
  --start-time $(date -u -d '24 hours ago' +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --period 3600 \
  --statistics Sum
```

---

## Step 5: RESOLVE — Fix It

### Common Issue 1: ETL Failed Due to API Timeout
**Symptoms:** `requests.exceptions.Timeout` in logs
**Fix:**
```bash
# Re-run ETL pipeline manually
python scripts/etl_pipeline.py --date $(date +%Y-%m-%d) --force
```

### Common Issue 2: S3 Permission Error
**Symptoms:** `AccessDenied` in logs
**Fix:**
```bash
# Check IAM role permissions
aws iam simulate-principal-policy \
  --policy-source-arn arn:aws:iam::123456789:role/it-enablement-lambda-role \
  --action-names s3:PutObject \
  --resource-arns arn:aws:s3:::it-enablement-prod-data-lake/*
```

### Common Issue 3: Data Quality Failure
**Symptoms:** ETL ran but Power BI shows 0 rows
**Fix:**
```bash
# Check processed data in S3
aws s3 ls s3://it-enablement-prod-data-lake/processed/transactions/$(date +%Y-%m-%d)/

# Re-run transformation only (skip extraction)
python scripts/etl_pipeline.py --skip-extract --date $(date +%Y-%m-%d)
```

### Common Issue 4: CloudWatch Alarm False Positive
**Symptoms:** Alarm fired but ETL actually succeeded
**Fix:**
```bash
# Manually set alarm back to OK state
aws cloudwatch set-alarm-state \
  --alarm-name "it-enablement-etl-failure" \
  --state-value OK \
  --state-reason "Manual reset — ETL confirmed successful"
```

---

## Step 6: VERIFY — Confirm It's Fixed

```bash
# 1. Check ETL completed successfully
aws logs filter-log-events \
  --log-group-name "/it-enablement/prod/etl-pipeline" \
  --filter-pattern "ETL PIPELINE COMPLETED SUCCESSFULLY"

# 2. Verify data is in S3
aws s3 ls s3://it-enablement-prod-data-lake/curated/reports/$(date +%Y-%m-%d)/

# 3. Check CloudWatch alarms are green
aws cloudwatch describe-alarms \
  --alarm-names "it-enablement-etl-failure" \
  --query "MetricAlarms[].StateValue"
```

---

## Step 7: DOCUMENT — Write It Down

After every P1/P2 incident, write a short post-mortem:

```
INCIDENT POST-MORTEM
====================
Date: 
Duration: 
Severity: 
Engineer: Selvathalapathy

What happened:
[Describe the issue in 2-3 sentences]

Root cause:
[Why did it happen?]

Impact:
[Which reports were affected? How many users?]

Resolution:
[What steps fixed it?]

Prevention:
[What will we do so this doesn't happen again?]
```

---

## Emergency Contacts

| Role | Name | Contact |
|------|------|---------|
| IT Enablement Engineer | Selvathalapathy | +65 8435 8234 |
| AWS Support | - | console.aws.amazon.com/support |

---

*This runbook should be reviewed and updated after every major incident.*
*Last updated: March 2026*
