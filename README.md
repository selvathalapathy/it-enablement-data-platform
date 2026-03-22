# 🏦 IT Enablement Data Platform

> **Production-ready IT Enablement platform — ETL pipelines, Power BI reporting, AWS infrastructure, DevSecOps automation and CloudWatch monitoring.**
> Built to support financial services operations similar to payment clearing infrastructure (FAST, PayNow, GIRO, SGQR).

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![AWS](https://img.shields.io/badge/AWS-FF9900?style=for-the-badge&logo=amazon-aws&logoColor=white)
![Terraform](https://img.shields.io/badge/Terraform-7B42BC?style=for-the-badge&logo=terraform&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-2088FF?style=for-the-badge&logo=github-actions&logoColor=white)
![Power BI](https://img.shields.io/badge/Power_BI-F2C811?style=for-the-badge&logo=powerbi&logoColor=black)

---

## 🎯 What This Platform Does

Imagine a bank's payment system processing thousands of transactions every day. This platform:

1. **Extracts** transaction data from REST APIs and databases
2. **Transforms** and cleans the data using Python ETL pipelines
3. **Loads** it into AWS S3 data lake for storage
4. **Visualises** it in Power BI dashboards for business stakeholders
5. **Monitors** infrastructure health using AWS CloudWatch
6. **Alerts** the team when something goes wrong
7. **Automates** deployments using GitHub Actions DevSecOps pipelines

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    DATA SOURCES                              │
│  REST APIs  │  Databases  │  CSV Files  │  Event Streams    │
└──────────────────────┬──────────────────────────────────────┘
                       │ Extract
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                 ETL PIPELINE (Python)                        │
│   Extract → Clean → Transform → Validate → Load             │
└──────────────────────┬──────────────────────────────────────┘
                       │ Load
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              AWS DATA LAKE (S3 + Lambda)                     │
│   Raw Zone → Processed Zone → Curated Zone                  │
└──────────┬────────────────────────────┬─────────────────────┘
           │ Report                     │ Monitor
           ▼                            ▼
┌──────────────────┐        ┌──────────────────────────────────┐
│   POWER BI       │        │   AWS CLOUDWATCH                 │
│   Dashboards     │        │   Metrics + Alerts + Runbooks    │
│   KPIs + Charts  │        │                                  │
└──────────────────┘        └──────────────────────────────────┘
```

---

## 📂 Project Structure

```
it-enablement-data-platform/
│
├── .github/workflows/          # DevSecOps CI/CD pipelines
│   ├── etl-pipeline.yml        # Automated ETL deployment
│   └── devsecops.yml           # Security scanning + deploy
│
├── terraform/                  # AWS Infrastructure as Code
│   ├── main.tf                 # S3, Lambda, CloudWatch, VPC
│   ├── variables.tf
│   └── outputs.tf
│
├── scripts/                    # Python ETL + REST API scripts
│   ├── etl_pipeline.py         # Main ETL pipeline
│   ├── api_extractor.py        # REST API data extraction
│   ├── data_transformer.py     # Data cleaning + transformation
│   └── cloudwatch_monitor.py  # CloudWatch metrics publisher
│
├── powerbi/                    # Power BI architecture + data
│   ├── DASHBOARD_GUIDE.md      # How to build the dashboards
│   ├── sample_data.csv         # Sample transaction data
│   └── dax_measures.md         # DAX formulas for KPIs
│
├── monitoring/                 # CloudWatch monitoring setup
│   └── cloudwatch_alerts.py   # Alerts + notification setup
│
├── runbooks/                   # Incident management guides
│   ├── INCIDENT_RESPONSE.md   # Step-by-step incident guide
│   └── RUNBOOK_ETL_FAILURE.md # ETL failure runbook
│
└── data/                       # Sample datasets
    └── transactions_sample.csv
```

---

## 🚀 Quick Start

```bash
# Clone the repo
git clone https://github.com/selvathalapathy/it-enablement-data-platform

# Install Python dependencies
pip install -r requirements.txt

# Set up AWS credentials
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret

# Deploy AWS infrastructure
cd terraform && terraform init && terraform apply

# Run ETL pipeline
python scripts/etl_pipeline.py

# Set up CloudWatch monitoring
python monitoring/cloudwatch_alerts.py
```

---

## 📊 Power BI Dashboards

See [powerbi/DASHBOARD_GUIDE.md](powerbi/DASHBOARD_GUIDE.md) for full setup guide.

**3 dashboards included:**
- Daily Transaction Summary — KPIs, volumes, success rates
- Weekly Trend Analysis — charts, comparisons, anomalies
- System Health Dashboard — uptime, error rates, SLA tracking

---

## 🔒 DevSecOps Pipeline

Every code push triggers:
1. **Security scan** — checks for vulnerabilities
2. **Unit tests** — validates ETL logic
3. **Linting** — code quality check
4. **Deploy** — pushes to AWS with manual approval for production

---

## 📋 Incident Runbooks

| Runbook | When to use |
|---------|------------|
| [ETL Pipeline Failure](runbooks/RUNBOOK_ETL_FAILURE.md) | ETL job fails or data missing |
| [Incident Response](runbooks/INCIDENT_RESPONSE.md) | Production incident detected |

---

## 🏆 Built By

**Selvathalapathy** — Senior IT Enablement & DevSecOps Engineer
- 10+ years experience in financial services IT operations
- Certified: CKA | AZ-400 | Power BI Data Analyst (PL-300)
- LinkedIn: [linkedin.com/in/selvathalapathy](https://linkedin.com/in/selvathalapathy)
