import pytest
from tools.grid_tools import evaluate_cedar_policy
from auth.jwt_verifier import create_simulated_cognito_token, verify_cognito_jwt
from fastapi.security import HTTPAuthorizationCredentials

def test_same_zone_hazard_permits_trip():
    res = evaluate_cedar_policy(
        action_name="TripFeederRelay",
        water_level_cm=26.0,
        neutral_amps=15.0,
        phase_r_volts=220.0,
        oil_temp=50.0,
        operator_zone="Kothrud",
        transformer_zone="Kothrud"
    )
    assert res["decision"] == "ALLOW"

def test_cross_zone_unauthorized_rejection():
    # Shivajinagar engineer attempting to trip Kothrud transformer is rejected by Cedar invariant
    res = evaluate_cedar_policy(
        action_name="TripFeederRelay",
        water_level_cm=30.0,
        neutral_amps=50.0,
        phase_r_volts=10.0,
        oil_temp=50.0,
        operator_zone="Shivajinagar",
        transformer_zone="Kothrud"
    )
    assert res["decision"] == "DENY"

def test_jwt_claim_verification():
    token = create_simulated_cognito_token(username="er_patil", role="WardEngineer", zone="Kothrud")
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    claims = verify_cognito_jwt(creds)
    assert claims["cognito:username"] == "er_patil"
    assert claims["custom:zone"] == "Kothrud"
