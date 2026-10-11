import json
from tools.grid_tools import (
    evaluate_cedar_policy,
    simulate_feeder_isolation,
    generate_lineman_dispatch,
)

class JalVidyutAgent:
    def __init__(self):
        self.system_prompt = (
            "JalVidyut autonomous monsoon flood and transformer safety agent. "
            "Evaluates Cedar policies before tripping relays and dispatches emergency crews."
        )

    def process_telemetry(self, telemetry: dict) -> dict:
        transformer_id = telemetry.get("transformerId", "UNKNOWN_DP")
        water_level_cm = telemetry.get("waterLevelCm", 0.0)
        neutral_amps = telemetry.get("neutralCurrentAmps", 0.0)
        phase_r_volts = telemetry.get("voltageVolts", {}).get("R", 230.0)
        oil_temp = telemetry.get("oilTemperatureCelsius", 45.0)

        trace_log = [
            f"Ingested telemetry for {transformer_id}: FloodWater={water_level_cm}cm, Neutral={neutral_amps}A, PhaseR={phase_r_volts}V, Temp={oil_temp}°C"
        ]

        # Anomaly classification
        is_hazard = water_level_cm > 20.0 or neutral_amps > 40.0 or phase_r_volts < 50.0

        if not is_hazard:
            trace_log.append("Status: DP nominal and within dry limits. No safety trip authorized.")
            return {
                "status": "HEALTHY",
                "cedarDecision": "NONE",
                "actions": [],
                "trace": trace_log,
            }

        trace_log.append("CRITICAL: Street waterlogging immersion / ground surge detected.")
        trace_log.append("Evaluating AWS Cedar Policy for Action::TripFeederRelay...")

        cedar_check = evaluate_cedar_policy("TripFeederRelay", water_level_cm, neutral_amps, phase_r_volts, oil_temp)
        trace_log.append(f"Cedar Policy Decision: {cedar_check['decision']} (Reasons: {cedar_check['reasons']})")

        actions_taken = []
        if cedar_check["decision"] == "ALLOW":
            trip_result = simulate_feeder_isolation(
                transformer_id, 
                f"Emergency autonomous trip: water level at {water_level_cm}cm exceeded 20cm safety boundary."
            )
            actions_taken.append(trip_result)

            parts = [
                "IP68 Waterproof Terminal Boot",
                "100A Horn-Gap Fuse Kit",
                "Silica Gel Dehydrating Breather",
            ]
            dispatch_result = generate_lineman_dispatch(transformer_id, "MONSOON_INUNDATION_GROUND_FAULT", parts)
            actions_taken.append(dispatch_result)
            trace_log.append(f"Dispatched Lineman work order: {dispatch_result['ticketId']}")
        else:
            trace_log.append("BLOCKED: Cedar policy denied relay isolation.")

        return {
            "status": "INCIDENT_RESOLVED" if cedar_check["decision"] == "ALLOW" else "INCIDENT_BLOCKED",
            "cedarDecision": cedar_check["decision"],
            "actions": actions_taken,
            "trace": trace_log,
        }
