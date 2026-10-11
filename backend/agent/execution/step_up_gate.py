import time
import uuid
from typing import Dict, Any, Optional

DELAY_WINDOW_SECONDS = 60

class StepUpGateController:
    def __init__(self):
        self.pending_tokens: Dict[str, Dict[str, Any]] = {}

    def create_step_up_token(self, transformer_id: str, water_cm: float, zone: str) -> Dict[str, Any]:
        token_id = f"STPP-${uuid.uuid4().hex[:8].upper()}"
        expiry_time = time.time() + DELAY_WINDOW_SECONDS
        record = {
            "tokenId": token_id,
            "transformerId": transformer_id,
            "zone": zone,
            "waterLevelCm": water_cm,
            "createdAt": time.time(),
            "expiresAt": expiry_time,
            "status": "PENDING_HUMAN_APPROVAL"
        }
        self.pending_tokens[token_id] = record
        return record

    def resolve_token(self, token_id: str, approved: bool) -> Dict[str, Any]:
        record = self.pending_tokens.get(token_id)
        if not record:
            return {"status": "ERROR", "message": "Step-up token not found or already consumed."}

        if time.time() > record["expiresAt"]:
            del self.pending_tokens[token_id]
            return {"status": "EXPIRED", "message": "Step-up authorization window expired."}

        del self.pending_tokens[token_id]
        new_status = "APPROVED_BY_OPERATOR" if approved else "REJECTED_BY_OPERATOR"
        record["status"] = new_status
        return {
            "status": "success",
            "decision": "ALLOW" if approved else "DENY",
            "transformerId": record["transformerId"],
            "record": record
        }

step_up_gate = StepUpGateController()
