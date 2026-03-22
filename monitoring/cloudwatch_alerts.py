"""
AWS CloudWatch Monitoring — IT Enablement Data Platform
========================================================

SIMPLE EXPLANATION (like you're in school):
CloudWatch = A school security guard who watches everything.
- If a student is late (system slow), the guard notices
- If someone breaks a rule (error occurs), the guard raises an alarm
- The guard keeps a diary (logs) of everything that happens

This script sets up CloudWatch to:
1. Watch how the ETL pipeline is performing
2. Send alerts when something goes wrong
3. Create dashboards showing system health
"""

import boto3
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

AWS_REGION = "ap-southeast-1"  # Singapore region
SNS_TOPIC_ARN = "arn:aws:sns:ap-southeast-1:123456789:it-enablement-alerts"


class CloudWatchMonitor:
    """
    Sets up and manages CloudWatch monitoring for IT Enablement platform.

    Simple explanation: Like setting up a camera system in a school.
    You decide what to watch, what triggers an alarm, and who gets notified.
    """

    def __init__(self):
        self.cloudwatch = boto3.client('cloudwatch', region_name=AWS_REGION)
        self.logs_client = boto3.client('logs', region_name=AWS_REGION)
        self.sns_client = boto3.client('sns', region_name=AWS_REGION)

    def create_etl_alarms(self):
        """
        Create alarms for ETL pipeline monitoring.

        Simple explanation: Like setting a fire alarm in school.
        If something bad happens (ETL fails, too slow, data missing),
        the alarm goes off and sends a message to the team.

        Types of alarms we set:
        1. ETL Failed — pipeline crashed
        2. ETL Too Slow — taking longer than expected
        3. No Data — pipeline ran but processed 0 rows (something wrong)
        4. High Error Rate — too many failed transactions
        """

        alarms = [
            # Alarm 1: ETL Pipeline Failed
            # Like a fire alarm — triggers immediately if ETL crashes
            {
                "AlarmName": "ETL-Pipeline-Failed",
                "AlarmDescription": "Triggers when ETL pipeline fails to complete successfully",
                "MetricName": "ETLSuccess",
                "Namespace": "ITEnablement/ETL",
                "Statistic": "Sum",
                "Period": 3600,        # Check every 1 hour
                "EvaluationPeriods": 1,
                "Threshold": 1,
                "ComparisonOperator": "LessThanThreshold",  # Alert if success < 1 (i.e. = 0 = failed)
                "TreatMissingData": "breaching",
                "Dimensions": [{"Name": "Pipeline", "Value": "TransactionETL"}],
                "AlarmActions": [SNS_TOPIC_ARN],  # Who to notify
            },

            # Alarm 2: ETL Processing Too Slow
            # Like a teacher noticing a student taking too long on an exam
            {
                "AlarmName": "ETL-Duration-Too-High",
                "AlarmDescription": "ETL pipeline taking longer than 30 minutes",
                "MetricName": "ETLDurationSeconds",
                "Namespace": "ITEnablement/ETL",
                "Statistic": "Average",
                "Period": 3600,
                "EvaluationPeriods": 1,
                "Threshold": 1800,     # 30 minutes = 1800 seconds
                "ComparisonOperator": "GreaterThanThreshold",
                "Dimensions": [{"Name": "Pipeline", "Value": "TransactionETL"}],
                "AlarmActions": [SNS_TOPIC_ARN],
            },

            # Alarm 3: No Data Processed
            # Like a teacher noticing no homework was submitted
            {
                "AlarmName": "ETL-Zero-Rows-Processed",
                "AlarmDescription": "ETL ran but processed 0 rows — possible data source issue",
                "MetricName": "ETLRowsProcessed",
                "Namespace": "ITEnablement/ETL",
                "Statistic": "Sum",
                "Period": 86400,       # Check daily
                "EvaluationPeriods": 1,
                "Threshold": 1,
                "ComparisonOperator": "LessThanThreshold",
                "TreatMissingData": "breaching",
                "Dimensions": [{"Name": "Pipeline", "Value": "TransactionETL"}],
                "AlarmActions": [SNS_TOPIC_ARN],
            },
        ]

        for alarm in alarms:
            try:
                self.cloudwatch.put_metric_alarm(**alarm)
                logger.info(f"Created alarm: {alarm['AlarmName']}")
            except Exception as e:
                logger.error(f"Failed to create alarm {alarm['AlarmName']}: {e}")

    def create_cloudwatch_dashboard(self):
        """
        Create CloudWatch dashboard for IT Enablement platform.

        Simple explanation: Like a school notice board showing:
        - How many students attended today (transactions processed)
        - How many were late (errors)
        - What the average grade was (success rate)

        This dashboard is visible in AWS Console — a single screen
        showing everything about the platform's health.
        """

        dashboard_body = {
            "widgets": [
                # Widget 1: ETL Success Rate
                # Big number showing if ETL is passing or failing
                {
                    "type": "metric",
                    "properties": {
                        "title": "ETL Pipeline Success Rate",
                        "metrics": [
                            ["ITEnablement/ETL", "ETLSuccess", "Pipeline", "TransactionETL"]
                        ],
                        "period": 3600,
                        "stat": "Sum",
                        "view": "timeSeries"
                    }
                },

                # Widget 2: Rows Processed Per Day
                # Bar chart showing how much data was processed
                {
                    "type": "metric",
                    "properties": {
                        "title": "Transaction Rows Processed Daily",
                        "metrics": [
                            ["ITEnablement/ETL", "ETLRowsProcessed", "Pipeline", "TransactionETL"]
                        ],
                        "period": 86400,
                        "stat": "Sum",
                        "view": "bar"
                    }
                },

                # Widget 3: ETL Duration Trend
                # Line chart showing if pipeline is getting slower over time
                {
                    "type": "metric",
                    "properties": {
                        "title": "ETL Pipeline Duration (seconds)",
                        "metrics": [
                            ["ITEnablement/ETL", "ETLDurationSeconds", "Pipeline", "TransactionETL"]
                        ],
                        "period": 3600,
                        "stat": "Average",
                        "view": "timeSeries"
                    }
                },

                # Widget 4: Alarm Status
                # Red/Green status showing all alarms at a glance
                {
                    "type": "alarm",
                    "properties": {
                        "title": "System Health Alarms",
                        "alarms": [
                            f"arn:aws:cloudwatch:{AWS_REGION}:123456789:alarm:ETL-Pipeline-Failed",
                            f"arn:aws:cloudwatch:{AWS_REGION}:123456789:alarm:ETL-Duration-Too-High",
                            f"arn:aws:cloudwatch:{AWS_REGION}:123456789:alarm:ETL-Zero-Rows-Processed",
                        ]
                    }
                }
            ]
        }

        try:
            self.cloudwatch.put_dashboard(
                DashboardName="IT-Enablement-Platform",
                DashboardBody=json.dumps(dashboard_body)
            )
            logger.info("CloudWatch dashboard created: IT-Enablement-Platform")
        except Exception as e:
            logger.error(f"Failed to create dashboard: {e}")

    def get_etl_health_report(self) -> Dict:
        """
        Get current health report of ETL pipeline.

        Simple explanation: Like asking the teacher for a student's
        current progress report — how many assignments done, any failures?
        """
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=24)

        metrics_to_check = [
            ("ETLSuccess", "Sum"),
            ("ETLRowsProcessed", "Sum"),
            ("ETLDurationSeconds", "Average"),
        ]

        health_report = {
            "report_time": datetime.now().isoformat(),
            "period": "Last 24 hours",
            "metrics": {}
        }

        for metric_name, stat in metrics_to_check:
            try:
                response = self.cloudwatch.get_metric_statistics(
                    Namespace="ITEnablement/ETL",
                    MetricName=metric_name,
                    Dimensions=[{"Name": "Pipeline", "Value": "TransactionETL"}],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=86400,
                    Statistics=[stat]
                )

                datapoints = response.get("Datapoints", [])
                value = datapoints[0].get(stat, 0) if datapoints else 0
                health_report["metrics"][metric_name] = value

            except Exception as e:
                logger.warning(f"Could not get metric {metric_name}: {e}")
                health_report["metrics"][metric_name] = "N/A"

        # Add health status
        etl_success = health_report["metrics"].get("ETLSuccess", 0)
        health_report["status"] = "HEALTHY" if etl_success >= 1 else "UNHEALTHY"
        health_report["status_emoji"] = "✅" if etl_success >= 1 else "🔴"

        return health_report

    def publish_custom_metric(self, metric_name: str, value: float, unit: str = "Count"):
        """
        Publish a custom metric to CloudWatch.

        Simple explanation: Like a student handing in their homework
        to the teacher (CloudWatch). The teacher records it in the gradebook.
        """
        try:
            self.cloudwatch.put_metric_data(
                Namespace="ITEnablement/Custom",
                MetricData=[{
                    "MetricName": metric_name,
                    "Value": value,
                    "Unit": unit,
                    "Timestamp": datetime.utcnow()
                }]
            )
            logger.info(f"Published metric: {metric_name} = {value} {unit}")
        except Exception as e:
            logger.error(f"Failed to publish metric {metric_name}: {e}")


def setup_monitoring():
    """
    Main setup function — runs once to configure all monitoring.

    Simple explanation: Like the first day of school setup —
    put up the notice boards, set the alarm bells, assign the guards.
    """
    logger.info("Setting up IT Enablement Platform monitoring...")

    monitor = CloudWatchMonitor()

    # Create all alarms
    logger.info("Creating CloudWatch alarms...")
    monitor.create_etl_alarms()

    # Create dashboard
    logger.info("Creating CloudWatch dashboard...")
    monitor.create_cloudwatch_dashboard()

    # Get initial health report
    logger.info("Getting initial health report...")
    health = monitor.get_etl_health_report()

    logger.info("=" * 50)
    logger.info(f"Platform Status: {health['status_emoji']} {health['status']}")
    for metric, value in health['metrics'].items():
        logger.info(f"  {metric}: {value}")
    logger.info("=" * 50)

    logger.info("Monitoring setup complete!")
    return health


if __name__ == "__main__":
    setup_monitoring()
