import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from sentinel.sensor_sentinel import SensorAnomalySentinel
from agent import JalVidyutAgent

def test_stuck_float_anomaly_detection():
    sentinel = SensorAnomalySentinel()
    telemetry = {
        "transformerId": "DP-PUNE-TEST-001",
        "waterLevelCm": 24.5,
        "neutralCurrentAmps": 0.0,
        "voltageVolts": {"R": 230.0, "Y": 230.0, "B": 230.0},
        "oilTemperatureCelsius": 30.0
    }
    audit = sentinel.audit_telemetry(telemetry)
    assert not audit["isValid"]
    assert "ANOMALY_STUCK_FLOAT_SUSPECTED" in audit["flags"]
    assert audit["recommendedAction"] == "HALT_EVALUATION"


def test_severed_ct_lead_detection():
    sentinel = SensorAnomalySentinel()
    telemetry = {
        "transformerId": "DP-PUNE-TEST-002",
        "waterLevelCm": 25.0,
        "neutralCurrentAmps": 0.0,
        "voltageVolts": {"R": 225.0, "Y": 220.0, "B": 220.0},
        "oilTemperatureCelsius": 48.0
    }
    audit = sentinel.audit_telemetry(telemetry)
    assert not audit["isValid"]
    assert "ANOMALY_SEVERED_CT_LEAD" in audit["flags"]


def test_water_rate_of_change_jitter_breach():
    sentinel = SensorAnomalySentinel()
    t1 = {
        "transformerId": "DP-PUNE-TEST-003",
        "waterLevelCm": 5.0,
        "neutralCurrentAmps": 10.0,
        "voltageVolts": {"R": 230.0},
        "oilTemperatureCelsius": 45.0
    }
    sentinel.audit_telemetry(t1)

    # Impossible 22cm surge within milliseconds
    t2 = {
        "transformerId": "DP-PUNE-TEST-003",
        "waterLevelCm": 27.0,
        "neutralCurrentAmps": 10.0,
        "voltageVolts": {"R": 230.0},
        "oilTemperatureCelsius": 45.0
    }
    audit2 = sentinel.audit_telemetry(t2)
    assert not audit2["isValid"]
    assert "ANOMALY_WATER_LEVEL_RATE_BREACH" in audit2["flags"]


def test_end_to_end_agent_halts_trip_on_sensor_fault():
    agent = JalVidyutAgent()
    faulty_telemetry = {
        "transformerId": "DP-PUNE-KOTHRUD-042",
        "zone": "Kothrud",
        "waterLevelCm": 25.0,
        "neutralCurrentAmps": 0.0,
        "voltageVolts": {"R": 230.0, "Y": 230.0, "B": 230.0},
        "oilTemperatureCelsius": 30.0
    }
    res = agent.process_telemetry(faulty_telemetry)
    assert res["status"] == "SENSOR_FAULT_HALTED"
    assert res["cedarDecision"] == "NONE"
    assert any(
        a.get("faultType") == "SENSOR_TRANSDUCER_FAULT" or a.get("reason") == "SENSOR_TRANSDUCER_FAULT"
        for a in res["actions"]
    )
