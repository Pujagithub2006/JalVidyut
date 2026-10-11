import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from agent import JalVidyutAgent
from execution.step_up_gate import step_up_gate

agent = JalVidyutAgent()

def test_borderline_water_triggers_step_up():
    telemetry = {
        "transformerId": "DP-PUNE-KOTHRUD-042",
        "zone": "Kothrud",
        "waterLevelCm": 18.0,
        "neutralCurrentAmps": 15.0,
        "voltageVolts": {"R": 220.0, "Y": 220.0, "B": 220.0},
        "oilTemperatureCelsius": 50.0
    }
    result = agent.process_telemetry(telemetry, operator_context={"zone": "Kothrud", "role": "WardEngineer"})
    
    assert result["status"] == "STEP_UP_REQUIRED"
    assert result["cedarDecision"] == "STEP_UP"
    assert "stepUpToken" in result
    assert result["stepUpToken"]["status"] == "PENDING_HUMAN_APPROVAL"

def test_step_up_approval_execution():
    token = step_up_gate.create_step_up_token("DP-PUNE-KOTHRUD-042", 18.0, "Kothrud")
    token_id = token["tokenId"]

    resolved_res = step_up_gate.resolve_token(token_id, approved=True)
    assert resolved_res["status"] == "success"
    assert resolved_res["decision"] == "ALLOW"

def test_catastrophic_water_bypasses_step_up_to_auto_allow():
    telemetry = {
        "transformerId": "DP-PUNE-KOTHRUD-042",
        "zone": "Kothrud",
        "waterLevelCm": 26.0,
        "neutralCurrentAmps": 15.0,
        "voltageVolts": {"R": 220.0, "Y": 220.0, "B": 220.0},
        "oilTemperatureCelsius": 50.0
    }
    result = agent.process_telemetry(telemetry, operator_context={"zone": "Kothrud", "role": "WardEngineer"})
    
    assert result["status"] == "INCIDENT_RESOLVED"
    assert result["cedarDecision"] == "ALLOW"
    assert any(a.get("relayState") == "OPEN" for a in result["actions"])
