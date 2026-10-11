import os
import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class NotificationDispatcher:
    def __init__(self, region_name: str = "us-east-1"):
        self.region = os.environ.get("AWS_DEFAULT_REGION", region_name)
        self.sns_topic_arn = os.environ.get("AWS_SNS_TOPIC_ARN")
        self.client = None
        try:
            import boto3
            self.client = boto3.client("sns", region_name=self.region)
        except Exception as e:
            logger.info("SNS client init fallback: %s", e)

    def dispatch_trip_alert(self, transformer_id: str, zone: str, reason: str, blast_radius: list) -> Dict[str, Any]:
        message_body = (
            f"🚨 [JALVIDYUT CRITICAL GRID ISOLATION]\n"
            f"Asset: {transformer_id}\n"
            f"Zone: {zone} Ward, Pune\n"
            f"Status: TRIP AUTHORIZED BY AWS CEDAR\n"
            f"Reason: {reason}\n"
            f"Quarantined Feeders: {', '.join(blast_radius)}\n"
            f"Action: Lineman emergency patrol dispatched."
        )

        ticket_id = f"TKT-JAL-{abs(hash(transformer_id + reason)) % 90000 + 10000}"
        result = {
            "ticketId": ticket_id,
            "message": message_body,
            "channel": "LOCAL_MOCK"
        }

        if self.client and self.sns_topic_arn and os.environ.get("AWS_ACCESS_KEY_ID"):
            try:
                res = self.client.publish(
                    TopicArn=self.sns_topic_arn,
                    Subject=f"JalVidyut Alert: {transformer_id} De-Energized",
                    Message=message_body
                )
                result["channel"] = "AWS_SNS_LIVE"
                result["snsMessageId"] = res.get("MessageId")
            except Exception as e:
                logger.warning("SNS publish fallback: %s", e)

        return result

    def dispatch_sensor_maintenance(self, transformer_id: str, anomalies: list) -> Dict[str, Any]:
        ticket_id = f"TKT-JAL-{abs(hash(transformer_id)) % 90000 + 10000}"
        message_body = (
            f"⚠️ [JALVIDYUT SENSOR ANOMALY TICKET]\n"
            f"Asset: {transformer_id}\n"
            f"Flags: {', '.join(anomalies)}\n"
            f"Action: Tripping suspended; sensor recalibration team dispatched."
        )
        return {
            "ticketId": ticket_id,
            "message": message_body,
            "channel": "SENSOR_CREW"
        }

notifier = NotificationDispatcher()
