import os
import time
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class DynamoDBAuditLogger:
    def __init__(self, table_name: str = "JalVidyut-Audit-Log", region_name: str = "us-east-1"):
        self.table_name = os.environ.get("DYNAMODB_TABLE_NAME", table_name)
        self.region = os.environ.get("AWS_DEFAULT_REGION", region_name)
        self.table = None
        try:
            import boto3
            dynamodb = boto3.resource("dynamodb", region_name=self.region)
            self.table = dynamodb.Table(self.table_name)
        except Exception as e:
            logger.info("DynamoDB client init fallback: %s", e)

    def log_decision(self, transformer_id: str, status: str, cedar_decision: str, telemetry: Dict[str, Any]) -> bool:
        if self.table and os.environ.get("AWS_ACCESS_KEY_ID"):
            try:
                item = {
                    "incidentId": f"{transformer_id}#{int(time.time()*1000)}",
                    "transformerId": transformer_id,
                    "timestamp": int(time.time()),
                    "status": status,
                    "cedarDecision": cedar_decision,
                    "waterLevelCm": str(telemetry.get("waterLevelCm")),
                    "neutralCurrentAmps": str(telemetry.get("neutralCurrentAmps"))
                }
                self.table.put_item(Item=item)
                return True
            except Exception as e:
                logger.warning("DynamoDB put_item fallback: %s", e)
        return False

dynamo_audit = DynamoDBAuditLogger()
