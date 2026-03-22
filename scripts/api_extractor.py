"""
REST API Data Extractor — IT Enablement Data Platform
======================================================

SIMPLE EXPLANATION (like you're in school):
REST API = A waiter at a restaurant.
- You (the script) tell the waiter what you want (request)
- The waiter goes to the kitchen (server) and gets it
- The waiter brings back your food (data) in JSON format

JSON = Like a neatly organised list:
{
  "name": "Selva",
  "age": 34,
  "city": "Singapore"
}

This script extracts transaction data from multiple REST APIs
and saves it to AWS S3 for the ETL pipeline to process.
"""

import requests
import boto3
import json
import logging
import time
from datetime import datetime, date
from typing import Dict, List, Optional
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class APIConfig:
    """
    API configuration — like a contact card for each data source.
    Each API has a URL, authentication key and how many records to get per page.
    """
    name: str
    base_url: str
    api_key: str
    page_size: int = 1000
    timeout: int = 30
    retry_attempts: int = 3


class RESTAPIExtractor:
    """
    Extracts data from REST APIs with retry logic and error handling.

    Simple explanation: Like a very persistent student who keeps asking
    the teacher for notes — if the teacher is busy (API error), the student
    waits a moment and tries again (retry logic).
    """

    def __init__(self, config: APIConfig):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        })

    def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """
        Make a single API request with retry logic.

        Simple explanation: Try to get the data. If it fails, wait a bit
        and try again. After 3 tries, give up and report the error.
        """
        url = f"{self.config.base_url}/{endpoint}"

        for attempt in range(self.config.retry_attempts):
            try:
                logger.info(f"API request attempt {attempt + 1}: {url}")
                response = self.session.get(url, params=params, timeout=self.config.timeout)
                response.raise_for_status()
                return response.json()

            except requests.exceptions.HTTPError as e:
                if response.status_code == 429:
                    # 429 = Too many requests — like being told "wait your turn"
                    wait_time = 2 ** attempt  # Wait 1s, 2s, 4s...
                    logger.warning(f"Rate limited. Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                elif response.status_code == 401:
                    logger.error("Authentication failed — check API key")
                    raise
                else:
                    if attempt == self.config.retry_attempts - 1:
                        raise
                    time.sleep(2 ** attempt)

            except requests.exceptions.ConnectionError:
                if attempt == self.config.retry_attempts - 1:
                    raise
                logger.warning(f"Connection error. Retrying in {2 ** attempt}s...")
                time.sleep(2 ** attempt)

        raise Exception(f"All {self.config.retry_attempts} attempts failed for {url}")

    def extract_transactions(self, start_date: str, end_date: str) -> List[Dict]:
        """
        Extract all transactions for a date range using pagination.

        Simple explanation: Imagine a library with 1000 books. Instead of
        carrying all 1000 at once (which is too heavy), you carry 100 at a time.
        Pagination = carrying data in small batches (pages).
        """
        all_records = []
        page = 1

        logger.info(f"Extracting transactions from {start_date} to {end_date}")

        while True:
            params = {
                "start_date": start_date,
                "end_date": end_date,
                "page": page,
                "page_size": self.config.page_size
            }

            response = self._make_request("transactions", params)

            # Get records from this page
            records = response.get("data", [])
            all_records.extend(records)

            logger.info(f"Page {page}: Got {len(records)} records. Total so far: {len(all_records)}")

            # Check if there are more pages
            # Like checking if there are more boxes to unpack
            total_pages = response.get("total_pages", 1)
            if page >= total_pages:
                break

            page += 1
            time.sleep(0.1)  # Small pause to be polite to the API

        logger.info(f"Extraction complete. Total records: {len(all_records)}")
        return all_records

    def extract_system_health(self) -> Dict:
        """
        Extract system health metrics from API.

        Simple explanation: Like asking a doctor for a health check report.
        Are all systems running? Any errors? How fast is everything?
        """
        logger.info("Extracting system health metrics...")
        return self._make_request("health/metrics")

    def extract_kpi_data(self, metric_names: List[str]) -> Dict:
        """
        Extract specific KPI metrics.

        Simple explanation: KPI = Key Performance Indicator.
        Like a school report card showing your grades in each subject.
        """
        logger.info(f"Extracting KPIs: {metric_names}")
        params = {"metrics": ",".join(metric_names)}
        return self._make_request("kpis", params)


def save_to_s3(data: List[Dict], bucket: str, key: str, aws_region: str = "ap-southeast-1"):
    """
    Save extracted data to AWS S3.

    Simple explanation: S3 is like a big filing cabinet in the cloud.
    We save the raw data here before cleaning it in the ETL pipeline.
    """
    s3_client = boto3.client('s3', region_name=aws_region)

    payload = {
        "extracted_at": datetime.now().isoformat(),
        "record_count": len(data),
        "data": data
    }

    try:
        s3_client.put_object(
            Bucket=bucket,
            Key=key,
            Body=json.dumps(payload, default=str),
            ContentType="application/json"
        )
        logger.info(f"Saved {len(data)} records to s3://{bucket}/{key}")
        return True
    except Exception as e:
        logger.error(f"Failed to save to S3: {e}")
        raise


def run_daily_extraction():
    """
    Main extraction job — runs daily to pull fresh data.

    Simple explanation: Like a milkman who comes every morning
    to deliver fresh milk (data). Every day at the same time,
    this script wakes up and collects new data.
    """
    today = str(date.today())
    logger.info(f"Starting daily extraction for {today}")

    # Configure the API connection
    api_config = APIConfig(
        name="TransactionAPI",
        base_url="https://api.example-payments.com/v1",
        api_key="your-api-key-here",  # In real life, this comes from AWS Secrets Manager
        page_size=1000
    )

    extractor = RESTAPIExtractor(api_config)

    try:
        # Extract today's transactions
        transactions = extractor.extract_transactions(
            start_date=today,
            end_date=today
        )

        # Save raw data to S3
        raw_key = f"raw/transactions/{today}/transactions_raw.json"
        save_to_s3(transactions, "bcs-data-platform", raw_key)

        # Extract system health
        health_data = extractor.extract_system_health()
        health_key = f"raw/health/{today}/system_health.json"
        save_to_s3([health_data], "bcs-data-platform", health_key)

        logger.info(f"Daily extraction completed successfully. {len(transactions)} transactions extracted.")

    except Exception as e:
        logger.error(f"Daily extraction failed: {e}")
        raise


if __name__ == "__main__":
    run_daily_extraction()
