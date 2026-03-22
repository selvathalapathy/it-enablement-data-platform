# 📊 Power BI Dashboard Guide — IT Enablement Platform

## Simple Explanation (like you're in school)

Power BI is like a **magic whiteboard** that reads data from a file or database
and automatically draws beautiful charts and tables.

Instead of manually making charts in Excel every day,
Power BI refreshes automatically and always shows the latest data.

---

## 3 Dashboards We Build

### Dashboard 1: Daily Transaction Summary
**Who uses it:** Operations team, managers
**Updated:** Every day automatically
**Shows:**
- Total transactions today
- Total value processed (SGD)
- Success rate %
- Failed transactions
- Transactions by channel (PayNow, FAST, GIRO)

### Dashboard 2: Weekly Trend Analysis
**Who uses it:** Senior management
**Updated:** Every Monday morning
**Shows:**
- Week-over-week transaction growth
- Peak hours heatmap
- Channel performance comparison
- Error rate trends

### Dashboard 3: System Health Dashboard
**Who uses it:** IT Operations team
**Updated:** Every hour
**Shows:**
- ETL pipeline status (Green/Red)
- Data freshness (when was last successful load?)
- Row counts per day
- CloudWatch alarm status

---

## How to Build Dashboard 1 — Step by Step

### Step 1: Connect to Data Source
1. Open Power BI Desktop
2. Click **Get Data** → **Amazon S3**
3. Enter bucket: `it-enablement-prod-data-lake`
4. Navigate to: `curated/reports/` folder
5. Select `daily_summary.csv`
6. Click **Load**

### Step 2: Build KPI Cards
KPI Card = A big number on the dashboard (like a scoreboard)

1. Click **Card** visual from the Visualisations panel
2. Drag `total_transactions` to the **Values** field
3. Rename to "Total Transactions Today"
4. Repeat for `total_amount`, `success_rate_pct`

### Step 3: Add Bar Chart — Transactions by Channel
1. Click **Clustered Bar Chart** visual
2. Drag `channel` to **Axis**
3. Drag `total_transactions` to **Values**
4. Format: Change colours, add data labels

### Step 4: Add Line Chart — Trend Over Time
1. Click **Line Chart** visual
2. Drag `transaction_date` to **Axis**
3. Drag `total_transactions` to **Values**
4. Add `total_amount` as second line

### Step 5: Add Donut Chart — Success vs Failure
1. Click **Donut Chart** visual
2. Drag `status` to **Legend**
3. Drag `total_transactions` to **Values**
4. Format: Green for SUCCESS, Red for FAILED

---

## DAX Measures (Key Formulas)
See [dax_measures.md](dax_measures.md) for all formulas.

**Most important measures:**

```dax
-- Success Rate %
Success Rate = 
DIVIDE(
    CALCULATE(SUM(transactions[total_transactions]), transactions[status] = "SUCCESS"),
    SUM(transactions[total_transactions]),
    0
) * 100

-- Daily Transaction Volume
Daily Volume = 
CALCULATE(
    SUM(transactions[total_amount]),
    DATESINPERIOD(transactions[transaction_date], LASTDATE(transactions[transaction_date]), -1, DAY)
)

-- Week over Week Growth %
WoW Growth = 
VAR ThisWeek = CALCULATE(SUM(transactions[total_transactions]), DATESINPERIOD(transactions[transaction_date], LASTDATE(transactions[transaction_date]), -7, DAY))
VAR LastWeek = CALCULATE(SUM(transactions[total_transactions]), DATESINPERIOD(transactions[transaction_date], LASTDATE(transactions[transaction_date]), -14, DAY))
RETURN DIVIDE(ThisWeek - LastWeek, LastWeek, 0) * 100
```

---

## Colour Scheme (BCS/NETS Brand)
| Colour | Hex | Use for |
|--------|-----|---------|
| Dark Red | `#C00000` | NETS brand, headers |
| White | `#FFFFFF` | Backgrounds |
| Dark Grey | `#404040` | Text |
| Green | `#00B050` | Success metrics |
| Red | `#FF0000` | Error/failure metrics |
| Blue | `#0070C0` | Neutral metrics |

---

## How to Schedule Automatic Refresh

1. Publish dashboard to Power BI Service (cloud)
2. Go to **Dataset Settings**
3. Click **Scheduled Refresh**
4. Set frequency: **Daily at 6:00 AM Singapore time**
5. This ensures the dashboard shows fresh data every morning before office hours
