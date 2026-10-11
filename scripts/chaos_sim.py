import sys
import os
from typing import Any, Dict, List

agent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend", "agent"))
if agent_dir not in sys.path:
    sys.path.insert(0, agent_dir)

from agent import JalVidyutAgent


class MonsoonChaosSimulator:
    def __init__(self):
        self.agent = JalVidyutAgent()

    def run_all_scenarios(self) -> List[Dict[str, Any]]:
        scenarios = [
            {
                "name": "SCENARIO_1_DRY_NOMINAL",
                "telemetry": {
                    "transformerId": "DP-PUNE-KOTHRUD-041",
                    "zone": "Kothrud",
                    "waterLevelCm": 4.5,
                    "neutralCurrentAmps": 1.2,
                    "voltageVolts": {"R": 230.0, "Y": 230.0, "B": 230.0},
                    "oilTemperatureCelsius": 42.0
                },
                "expected_status": "HEALTHY"
            },
            {
                "name": "SCENARIO_2_STUCK_FLOAT_SENSOR_CORRUPTION",
                "telemetry": {
                    "transformerId": "DP-PUNE-KOTHRUD-042",
                    "zone": "Kothrud",
                    "waterLevelCm": 24.0,
                    "neutralCurrentAmps": 0.0,
                    "voltageVolts": {"R": 230.0, "Y": 230.0, "B": 230.0},
                    "oilTemperatureCelsius": 28.0
                },
                "expected_status": "SENSOR_FAULT_HALTED"
            },
            {
                "name": "SCENARIO_3_BORDERLINE_WATER_HUMAN_GATE",
                "telemetry": {
                    "transformerId": "DP-PUNE-KOTHRUD-043",
                    "zone": "Kothrud",
                    "waterLevelCm": 18.0,
                    "neutralCurrentAmps": 12.0,
                    "voltageVolts": {"R": 220.0, "Y": 220.0, "B": 220.0},
                    "oilTemperatureCelsius": 48.0
                },
                "expected_status": "STEP_UP_REQUIRED"
            },
            {
                "name": "SCENARIO_4_CATASTROPHIC_DELUGE_LATERAL_SHUNT",
                "telemetry": {
                    "transformerId": "DP-PUNE-KOTHRUD-044",
                    "zone": "Kothrud",
                    "waterLevelCm": 28.5,
                    "neutralCurrentAmps": 49.2,
                    "voltageVolts": {"R": 210.0, "Y": 215.0, "B": 212.0},
                    "oilTemperatureCelsius": 54.0
                },
                "expected_status": "INCIDENT_RESOLVED"
            }
        ]

        results = []
        for sc in scenarios:
            res = self.agent.process_telemetry(sc["telemetry"], operator_context={"zone": "Kothrud", "role": "WardEngineer"})
            results.append({
                "scenario": sc["name"],
                "status": res["status"],
                "decision": res["cedarDecision"],
                "passed": res["status"] == sc["expected_status"]
            })
        return results


if __name__ == "__main__":
    sim = MonsoonChaosSimulator()
    print("Executing Pune Monsoon Chaos Injections...")
    for out in sim.run_all_scenarios():
        print(f"[{out['scenario']}] -> Status: {out['status']} (Match: {out['passed']})")
