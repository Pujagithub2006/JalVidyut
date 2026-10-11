import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from notifications.sns_dispatcher import sns_dispatcher
from agent import JalVidyutAgent

agent = JalVidyutAgent()


def test_lineman_sms_formatting():
    res = sns_dispatcher.dispatch_lineman_sms(
        phone_number="+919876543210",
        ticket_id="TKT-JAL-00042",
        transformer_id="DP-PUNE-KOTHRUD-042",
        zone="Kothrud",
        parts=["IP68 Terminal Boot", "100A Fuse"]
    )
    assert res["status"] in ["SENT_AWS_SNS", "SENT_LOCAL_SNS_PROXY"]
    assert "DP-PUNE-KOTHRUD-042" in res["message"]
    assert "IP68 Terminal Boot" in res["message"]


def test_public_ward_broadcast_structure():
    res = sns_dispatcher.broadcast_public_ward_alert(
        zone="Kothrud",
        transformer_id="DP-PKOT-01",
        reason="Street flooded 30cm depth."
    )
    assert res["status"] in ["SENT_AWS_SNS", "SENT_LOCAL_SNS_PROXY"]
    assert res["payload"]["alertClass"] == "CRITICAL_PUNE_GRID_SAFETY"
    assert res["payload"]["zone"] == "Kothrud"


def test_end_to_end_hazard_dispatches_notifications():
    telemetry = {
        "transformerId": "DP-PUNE-KOTHRUD-042",
        "zone": "Kothrud",
        "waterLevelCm": 27.0,
        "neutralCurrentAmps": 12.0,
        "voltageVolts": {"R": 220.0, "Y": 220.0, "B": 220.0},
        "oilTemperatureCelsius": 50.0
    }
    res = agent.process_telemetry(
        telemetry,
        operator_context={"zone": "Kothrud", "role": "WardEngineer"}
    )
    assert res["cedarDecision"] == "ALLOW"
    action_types = []
    for action in res["actions"]:
        if isinstance(action, dict):
            if "sms_notification" in action:
                action_types.append("sms_notification")
            if "ward_broadcast" in action:
                action_types.append("ward_broadcast")

    assert "sms_notification" in action_types
    assert "ward_broadcast" in action_types
