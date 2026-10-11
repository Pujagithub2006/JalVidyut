import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from tools.grid_tools import evaluate_cedar_policy
from intelligence.bedrock_risk import bedrock_scorer

def test_bedrock_risk_bounds_and_structure():
    telemetry = {"waterLevelCm": 14.0, "neutralCurrentAmps": 5.0, "zone": "Kothrud"}
    geo = {"elevationMeters": 540.0, "rainRateMmHr": 65.0}
    result = bedrock_scorer.calculate_surge_risk(telemetry, geographical_context=geo)
    assert 0.0 <= result["mlFloodSurgeRisk"] <= 1.0
    assert "reasoning" in result
    assert result["source"] in ["AWS_BEDROCK_CLAUDE", "HYDROL_SURGE_ENGINE"]

def test_borderline_water_low_risk_denies_trip():
    res = evaluate_cedar_policy(
        action_name="TripFeederRelay",
        water_level_cm=15.0,
        neutral_amps=10.0,
        phase_r_volts=225.0,
        oil_temp=50.0,
        operator_zone="Kothrud",
        transformer_zone="Kothrud",
        ml_flood_surge_risk=0.30
    )
    assert res["decision"] == "DENY"

def test_proactive_surge_permits_trip():
    res = evaluate_cedar_policy(
        action_name="TripFeederRelay",
        water_level_cm=15.0,
        neutral_amps=10.0,
        phase_r_volts=225.0,
        oil_temp=50.0,
        operator_zone="Kothrud",
        transformer_zone="Kothrud",
        ml_flood_surge_risk=0.92
    )
    assert res["decision"] == "ALLOW"
