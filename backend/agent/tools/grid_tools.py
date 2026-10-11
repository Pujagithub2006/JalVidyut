import os
from cedarpy import is_authorized, Decision

POLICY_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "policies", "grid_policies.cedar")
)

def evaluate_cedar_policy(
    action_name: str,
    water_level_cm: float,
    neutral_amps: float,
    phase_r_volts: float,
    oil_temp: float,
    operator_zone: str = "Kothrud",
    transformer_zone: str = "Kothrud",
    operator_role: str = "WardEngineer"
) -> dict:
    if not os.path.exists(POLICY_PATH):
        raise FileNotFoundError(f"Cedar policy file not found at: {POLICY_PATH}")

    with open(POLICY_PATH, "r", encoding="utf-8") as f:
        policies = f.read()

    request = {
        "principal": f'Role::"{operator_role}"',
        "action": f'Action::"{action_name}"',
        "resource": f'Transformer::"{transformer_zone}-042"',
        "context": {
            "waterLevelCm": int(round(water_level_cm)),
            "neutralCurrentAmps": int(round(neutral_amps)),
            "phaseRVolts": int(round(phase_r_volts)),
            "oilTempCelsius": int(round(oil_temp)),
            "operatorZone": operator_zone,
            "transformerZone": transformer_zone
        },
    }

    result = is_authorized(request, policies, entities=[])
    decision = "ALLOW" if result.decision == Decision.Allow else "DENY"

    return {
        "action": action_name,
        "decision": decision,
        "errors": [str(err) for err in result.diagnostics.errors],
        "reasons": [str(r) for r in result.diagnostics.reasons],
    }

def simulate_feeder_isolation(transformer_id: str, reason: str) -> dict:
    return {
        "status": "SUCCESS",
        "action": "TripFeederRelay",
        "target": transformer_id,
        "relayState": "OPEN",
        "reason": reason,
    }

def generate_lineman_dispatch(transformer_id: str, fault_type: str, required_parts: list) -> dict:
    return {
        "ticketId": f"TKT-JAL-{abs(hash(transformer_id)) % 100000:05d}",
        "transformerId": transformer_id,
        "faultType": fault_type,
        "partsManifest": required_parts,
        "priority": "P0_EMERGENCY",
        "status": "DISPATCHED",
    }
