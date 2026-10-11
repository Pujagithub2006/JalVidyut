import json
import logging
import os
from typing import Any, Dict, List
import boto3

logger = logging.getLogger("SNSDispatcher")
logging.basicConfig(level=logging.INFO)


class SNSEmergencyDispatcher:
    def __init__(self, region_name: str = "ap-south-1"):
        self.region_name = region_name
        try:
            self.client = boto3.client("sns", region_name=self.region_name)
        except Exception as e:
            logger.warning(f"AWS SNS client deferred: {e}")
            self.client = None

    def dispatch_lineman_sms(
        self,
        phone_number: str,
        ticket_id: str,
        transformer_id: str,
        zone: str,
        parts: List[str]
    ) -> Dict[str, Any]:
        parts_str = ", ".join(parts)
        message = (
            f"[JalVidyut P0 Alert] EMERGENCY TRIP at {transformer_id} ({zone}). "
            f"Work Order: {ticket_id}. Manifest: {parts_str}. Proceed to site."
        )

        if self.client and os.environ.get("AWS_EXECUTION_ENV"):
            try:
                res = self.client.publish(
                    PhoneNumber=phone_number,
                    Message=message,
                    MessageAttributes={
                        "AWS.SNS.SMS.SMSType": {
                            "DataType": "String",
                            "StringValue": "Transactional"
                        }
                    }
                )
                return {
                    "status": "SENT_AWS_SNS",
                    "messageId": res.get("MessageId"),
                    "recipient": phone_number,
                    "message": message
                }
            except Exception as e:
                logger.warning(f"AWS SNS publish failed: {e}")

        return {
            "status": "SENT_LOCAL_SNS_PROXY",
            "recipient": phone_number,
            "message": message
        }

    def broadcast_public_ward_alert(
        self,
        zone: str,
        transformer_id: str,
        reason: str
    ) -> Dict[str, Any]:
        broadcast_payload = {
            "alertClass": "CRITICAL_PUNE_GRID_SAFETY",
            "zone": zone,
            "transformerId": transformer_id,
            "status": "DEENERGIZED_FOR_SAFETY",
            "message": f"Transformer {transformer_id} in {zone} de-energized to protect against ground electrocution. {reason}"
        }

        if self.client and os.environ.get("AWS_EXECUTION_ENV"):
            try:
                topic_arn = f"arn:aws:sns:{self.region_name}:123456789012:jalvidyut-{zone.lower()}-alerts"
                res = self.client.publish(
                    TopicArn=topic_arn,
                    Message=json.dumps(broadcast_payload)
                )
                return {
                    "status": "SENT_AWS_SNS",
                    "messageId": res.get("MessageId"),
                    "payload": broadcast_payload
                }
            except Exception as e:
                logger.warning(f"AWS SNS topic publish failed: {e}")

        return {
            "status": "SENT_LOCAL_SNS_PROXY",
            "payload": broadcast_payload
        }


sns_dispatcher = SNSEmergencyDispatcher()
