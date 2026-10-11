import pytest
from tools.grid_tools import evaluate_cedar_policy

def test_flood_immersion_permits_trip():
    res = evaluate_cedar_policy(
        action_name="TripFeederRelay",
        water_level_cm=25.0,
        neutral_amps=10.0,
        phase_r_volts=220.0,
        oil_temp=50.0
    )
    assert res["decision"] == "ALLOW"

def test_neutral_ground_short_permits_trip():
    res = evaluate_cedar_policy(
        action_name="TripFeederRelay",
        water_level_cm=5.0,
        neutral_amps=48.0,
        phase_r_volts=0.0,
        oil_temp=55.0
    )
    assert res["decision"] == "ALLOW"

def test_safe_nominal_grid_denies_trip():
    res = evaluate_cedar_policy(
        action_name="TripFeederRelay",
        water_level_cm=2.0,
        neutral_amps=1.5,
        phase_r_volts=230.0,
        oil_temp=45.0
    )
    assert res["decision"] == "DENY"

def test_overheated_transformer_forbids_reset():
    res = evaluate_cedar_policy(
        action_name="ResetFeederRelay",
        water_level_cm=0.0,
        neutral_amps=0.5,
        phase_r_volts=230.0,
        oil_temp=78.0
    )
    assert res["decision"] == "DENY"
