import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from topology.grid_graph import grid_topology
from agent import JalVidyutAgent

agent = JalVidyutAgent()


def test_standard_hazard_triggers_local_isolation_only():
    perimeter = grid_topology.compute_quarantine_perimeter(
        transformer_id="DP-PUNE-KOTHRUD-042",
        neutral_leakage_amps=15.0
    )
    assert perimeter["isolationLevel"] == "LOCAL_ONLY"
    assert perimeter["quarantinedCircuits"] == ["DP-PUNE-KOTHRUD-042"]
    assert "Sahyadri Hospital Ring" in perimeter["protectedCriticalLoads"]


def test_extreme_leakage_triggers_lateral_ring_shunt():
    perimeter = grid_topology.compute_quarantine_perimeter(
        transformer_id="DP-PUNE-KOTHRUD-042",
        neutral_leakage_amps=48.5
    )
    assert perimeter["isolationLevel"] == "LATERAL_RING_SHUNT"
    assert "DP-PUNE-KOTHRUD-041" in perimeter["quarantinedCircuits"]
    assert "DP-PUNE-KOTHRUD-043" in perimeter["quarantinedCircuits"]


def test_end_to_end_topology_quarantine_included_in_actions():
    telemetry = {
        "transformerId": "DP-PUNE-KOTHRUD-042",
        "zone": "Kothrud",
        "waterLevelCm": 27.0,
        "neutralCurrentAmps": 49.0,
        "voltageVolts": {"R": 220.0, "Y": 220.0, "B": 220.0},
        "oilTemperatureCelsius": 50.0
    }
    res = agent.process_telemetry(
        telemetry,
        operator_context={"zone": "Kothrud", "role": "WardEngineer"}
    )
    assert res["status"] == "INCIDENT_RESOLVED"
    assert res["cedarDecision"] == "ALLOW"

    topo_action = next(a for a in res["actions"] if "topologyPerimeter" in a)
    assert topo_action["topologyPerimeter"]["isolationLevel"] == "LATERAL_RING_SHUNT"
