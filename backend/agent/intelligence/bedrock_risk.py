import json
import logging
import os
import boto3
from typing import Dict, Any

logger = logging.getLogger("BedrockRiskScorer")
logging.basicConfig(level=logging.INFO)

class BedrockRiskScorer:
    def __init__(self, region_name: str = "us-east-1", model_id: str = "anthropic.claude-3-haiku-20240307-v1:0"):
        self.region_name = region_name
        self.model_id = model_id
        try:
            self.client = boto3.client("bedrock-runtime", region_name=self.region_name)
        except Exception as e:
            logger.warning(f"AWS Bedrock client initialization deferred: {e}")
            self.client = None

    def calculate_surge_risk(self, telemetry: Dict[str, Any], geographical_context: Dict[str, Any] = None) -> Dict[str, Any]:
        water_cm = telemetry.get("waterLevelCm", 0.0)
        leakage_amps = telemetry.get("neutralCurrentAmps", 0.0)
        zone = telemetry.get("zone", "Kothrud")
        elevation_meters = geographical_context.get("elevationMeters", 560.0) if geographical_context else 560.0
        rain_rate_mm_hr = geographical_context.get("rainRateMmHr", 45.0) if geographical_context else 45.0

        prompt_text = (
            f"Analyze monsoon grid risk for distribution point in {zone}. "
            f"Water: {water_cm}cm, Leakage: {leakage_amps}A, Elevation: {elevation_meters}m, Rain: {rain_rate_mm_hr}mm/hr."
        )

        if self.client and os.environ.get("AWS_EXECUTION_ENV"):
            try:
                payload = {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 150,
                    "messages": [{"role": "user", "content": prompt_text}]
                }
                response = self.client.invoke_model(body=json.dumps(payload), modelId=self.model_id)
                response_body = json.loads(response.get("body").read())
                output_text = response_body.get("content", [{}])[0].get("text", "{}")
                parsed = json.loads(output_text)
                return {
                    "mlFloodSurgeRisk": min(max(float(parsed.get("mlFloodSurgeRisk", 0.5)), 0.0), 1.0),
                    "reasoning": str(parsed.get("reasoning", "Bedrock real-time analysis")),
                    "source": "AWS_BEDROCK_CLAUDE"
                }
            except Exception as e:
                logger.warning(f"Bedrock runtime call failed: {e}")

        elevation_factor = max(0.1, (600.0 - elevation_meters) / 100.0)
        rain_factor = min(1.0, rain_rate_mm_hr / 80.0)
        water_factor = min(1.0, water_cm / 25.0)
        computed_risk = round(min(1.0, (water_factor * 0.5) + (rain_factor * 0.3) + (elevation_factor * 0.2)), 2)
        reasoning = f"High surge potential in {zone} basin ({elevation_meters}m) under {rain_rate_mm_hr}mm/hr precipitation rate."

        return {
            "mlFloodSurgeRisk": computed_risk,
            "reasoning": reasoning,
            "source": "HYDROL_SURGE_ENGINE"
        }

bedrock_scorer = BedrockRiskScorer()
