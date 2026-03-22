"""
ETL Pipeline — IT Enablement Data Platform
==========================================

SIMPLE EXPLANATION (like you're in school):
- EXTRACT  = Go to the database/API and GET the data (like collecting homework)
- TRANSFORM = Clean and organise the data (like checking the homework for errors)
- LOAD     = Save the clean data to S3 (like filing the homework in the right folder)

This pipeline processes daily financial transactions (like PayNow, FAST, GIRO)
and prepares them for Power BI reporting.
"""

import boto3
import pandas as pd
import logging
import json
from datetime import datetime, date
from typing import Dict, List
import requests

# Set up logging — this is like a diary that records everything the script does
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ─── CONFIGURATION ────────────────────────────────────────────────────────────
# Think of this like settings — where to get data, where to save it
CONFIG = {
    "s3_bucket": "bcs-data-platform",          # S3 = Amazon's file storage
    "raw_prefix": "raw/transactions/",          # Raw = unprocessed data folder
    "processed_prefix": "processed/transactions/",  # Processed = clean data folder
    "curated_prefix": "curated/reports/",       # Curated = ready for Power BI
    "aws_region": "ap-southeast-1",             # Singapore AWS region
}


# ─── STEP 1: EXTRACT ──────────────────────────────────────────────────────────
# This is like going to the source and collecting raw data

def extract_from_api(api_url: str, api_key: str) -> List[Dict]:
    """
    Extract transaction data from REST API.

    Simple explanation: Imagine calling a waiter (API) at a restaurant
    and asking for today's menu (data). The waiter brings back all the items.
    """
    logger.info(f"Extracting data from API: {api_url}")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(
            api_url,
            headers=headers,
            params={"date": str(date.today()), "limit": 10000},
            timeout=30
        )
        response.raise_for_status()  # Raises error if request failed
        data = response.json()
        logger.info(f"Successfully extracted {len(data)} records from API")
        return data

    except requests.exceptions.RequestException as e:
        logger.error(f"API extraction failed: {e}")
        raise


def extract_from_s3(bucket: str, key: str) -> pd.DataFrame:
    """
    Extract data from S3 (Amazon file storage).

    Simple explanation: Like opening a file from a shared drive.
    S3 is Amazon's cloud version of a shared drive.
    """
    logger.info(f"Extracting data from S3: s3://{bucket}/{key}")

    s3_client = boto3.client('s3', region_name=CONFIG["aws_region"])

    try:
        response = s3_client.get_object(Bucket=bucket, Key=key)
        df = pd.read_csv(response['Body'])
        logger.info(f"Successfully extracted {len(df)} rows from S3")
        return df

    except Exception as e:
        logger.error(f"S3 extraction failed: {e}")
        raise


# ─── STEP 2: TRANSFORM ────────────────────────────────────────────────────────
# This is like a teacher checking homework — fixing mistakes, organising

def transform_transactions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and transform transaction data.

    Simple explanation: Raw data is messy — like a student's rough notes.
    Transform = rewrite those notes neatly so the teacher (Power BI) can read them.

    What we do:
    1. Remove duplicates (same transaction recorded twice — remove one)
    2. Fill missing values (empty cells — fill with sensible defaults)
    3. Convert data types (make sure numbers are numbers, dates are dates)
    4. Add calculated columns (like adding a "total" column in maths)
    5. Filter bad records (remove rows that don't make sense)
    """
    logger.info(f"Starting transformation. Input rows: {len(df)}")

    # Step 1: Remove duplicate transactions
    # Like removing duplicate names from a register
    initial_count = len(df)
    df = df.drop_duplicates(subset=['transaction_id'])
    logger.info(f"Removed {initial_count - len(df)} duplicate records")

    # Step 2: Handle missing values
    # Like filling in blank spaces in a form
    df['amount'] = df['amount'].fillna(0)
    df['status'] = df['status'].fillna('UNKNOWN')
    df['channel'] = df['channel'].fillna('OTHER')

    # Step 3: Convert data types
    # Like making sure all phone numbers are in the same format
    df['transaction_date'] = pd.to_datetime(df['transaction_date'])
    df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
    df['amount'] = df['amount'].fillna(0)

    # Step 4: Add calculated columns
    # Like adding a "Total" row at the bottom of a table
    df['transaction_year'] = df['transaction_date'].dt.year
    df['transaction_month'] = df['transaction_date'].dt.month
    df['transaction_day'] = df['transaction_date'].dt.day
    df['transaction_hour'] = df['transaction_date'].dt.hour
    df['day_of_week'] = df['transaction_date'].dt.day_name()
    df['is_weekend'] = df['transaction_date'].dt.dayofweek.isin([5, 6])

    # Step 5: Categorise transaction amounts
    # Like grading: Small / Medium / Large
    df['amount_category'] = pd.cut(
        df['amount'],
        bins=[0, 100, 1000, 10000, float('inf')],
        labels=['Small', 'Medium', 'Large', 'Very Large']
    )

    # Step 6: Calculate success rate flag
    df['is_successful'] = df['status'].isin(['SUCCESS', 'COMPLETED', 'APPROVED'])

    # Step 7: Remove records with negative amounts (data quality check)
    invalid_count = len(df[df['amount'] < 0])
    df = df[df['amount'] >= 0]
    logger.info(f"Removed {invalid_count} records with negative amounts")

    logger.info(f"Transformation complete. Output rows: {len(df)}")
    return df


def generate_daily_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate daily summary report.

    Simple explanation: Like a school report card — instead of showing
    every single homework, it shows the average grade for the whole month.
    """
    logger.info("Generating daily summary...")

    summary = df.groupby(['transaction_date', 'channel', 'status']).agg(
        total_transactions=('transaction_id', 'count'),
        total_amount=('amount', 'sum'),
        avg_amount=('amount', 'mean'),
        max_amount=('amount', 'max'),
        successful_count=('is_successful', 'sum')
    ).reset_index()

    # Calculate success rate percentage
    summary['success_rate_pct'] = (
        summary['successful_count'] / summary['total_transactions'] * 100
    ).round(2)

    logger.info(f"Daily summary generated: {len(summary)} rows")
    return summary


# ─── STEP 3: LOAD ─────────────────────────────────────────────────────────────
# This is like filing the clean homework in the right folder

def load_to_s3(df: pd.DataFrame, bucket: str, key: str) -> bool:
    """
    Load processed data to S3.

    Simple explanation: Like saving a finished Excel file to a shared drive
    so everyone in the office can access it.
    """
    logger.info(f"Loading {len(df)} rows to s3://{bucket}/{key}")

    s3_client = boto3.client('s3', region_name=CONFIG["aws_region"])

    try:
        # Convert DataFrame to CSV in memory
        csv_buffer = df.to_csv(index=False)

        # Upload to S3
        s3_client.put_object(
            Bucket=bucket,
            Key=key,
            Body=csv_buffer,
            ContentType='text/csv',
            Metadata={
                'row_count': str(len(df)),
                'processed_at': datetime.now().isoformat(),
                'pipeline_version': '1.0'
            }
        )

        logger.info(f"Successfully loaded data to S3: s3://{bucket}/{key}")
        return True

    except Exception as e:
        logger.error(f"S3 load failed: {e}")
        raise


def publish_etl_metrics(success: bool, row_count: int, duration_seconds: float):
    """
    Publish ETL metrics to AWS CloudWatch.

    Simple explanation: Like sending a report card to the principal (CloudWatch)
    so they know how the ETL pipeline performed today.
    """
    cloudwatch = boto3.client('cloudwatch', region_name=CONFIG["aws_region"])

    metrics = [
        {
            'MetricName': 'ETLSuccess',
            'Value': 1 if success else 0,
            'Unit': 'Count',
            'Dimensions': [{'Name': 'Pipeline', 'Value': 'TransactionETL'}]
        },
        {
            'MetricName': 'ETLRowsProcessed',
            'Value': row_count,
            'Unit': 'Count',
            'Dimensions': [{'Name': 'Pipeline', 'Value': 'TransactionETL'}]
        },
        {
            'MetricName': 'ETLDurationSeconds',
            'Value': duration_seconds,
            'Unit': 'Seconds',
            'Dimensions': [{'Name': 'Pipeline', 'Value': 'TransactionETL'}]
        }
    ]

    try:
        cloudwatch.put_metric_data(
            Namespace='ITEnablement/ETL',
            MetricData=metrics
        )
        logger.info("ETL metrics published to CloudWatch")
    except Exception as e:
        logger.warning(f"Failed to publish CloudWatch metrics: {e}")


# ─── MAIN PIPELINE ────────────────────────────────────────────────────────────

def run_etl_pipeline():
    """
    Main ETL pipeline orchestrator.

    Simple explanation: This is like the school timetable — it runs
    Extract → Transform → Load in order, and reports back whether
    everything went well.
    """
    start_time = datetime.now()
    logger.info("=" * 60)
    logger.info("IT Enablement ETL Pipeline — Starting")
    logger.info(f"Run date: {date.today()}")
    logger.info("=" * 60)

    try:
        # ── EXTRACT ──
        logger.info("STEP 1: EXTRACT — Getting raw data from S3...")
        today = str(date.today())
        raw_key = f"{CONFIG['raw_prefix']}{today}/transactions.csv"
        df_raw = extract_from_s3(CONFIG['s3_bucket'], raw_key)

        # ── TRANSFORM ──
        logger.info("STEP 2: TRANSFORM — Cleaning and processing data...")
        df_clean = transform_transactions(df_raw)
        df_summary = generate_daily_summary(df_clean)

        # ── LOAD ──
        logger.info("STEP 3: LOAD — Saving processed data to S3...")

        # Save cleaned transactions
        processed_key = f"{CONFIG['processed_prefix']}{today}/transactions_clean.csv"
        load_to_s3(df_clean, CONFIG['s3_bucket'], processed_key)

        # Save daily summary (this is what Power BI reads)
        summary_key = f"{CONFIG['curated_prefix']}{today}/daily_summary.csv"
        load_to_s3(df_summary, CONFIG['s3_bucket'], summary_key)

        # ── REPORT ──
        duration = (datetime.now() - start_time).total_seconds()
        logger.info("=" * 60)
        logger.info("ETL PIPELINE COMPLETED SUCCESSFULLY")
        logger.info(f"Rows processed: {len(df_clean)}")
        logger.info(f"Duration: {duration:.2f} seconds")
        logger.info("=" * 60)

        # Publish success metrics to CloudWatch
        publish_etl_metrics(True, len(df_clean), duration)
        return True

    except Exception as e:
        duration = (datetime.now() - start_time).total_seconds()
        logger.error(f"ETL PIPELINE FAILED: {e}")
        publish_etl_metrics(False, 0, duration)
        raise


if __name__ == "__main__":
    run_etl_pipeline()
