from tools.grid_tools import (
    evaluate_cedar_policy,
    simulate_feeder_isolation,
    generate_lineman_dispatch,
)

class JalVidyutAgent:
    def __init__(self):
        self.system_prompt = "JalVidyut autonomous monsoon flood safety agent."

    def process_telemetry(self, telemetry: dict, operator_context: dict = None) -> dict:
        transformer_id = telemetry.get("transformerId", "DP-PUNE-KOTHRUD-042")
        transformer_zone = telemetry.get("zone", "Kothrud")
        water_level_cm = telemetry.get("waterLevelCm", 0.0)
        neutral_amps = telemetry.get("neutralCurrentAmps", 0.0)
        phase_r_volts = telemetry.get("voltageVolts", {}).get("R", 230.0)
        oil_temp = telemetry.get("oilTemperatureCelsius", 45.0)

        operator_zone = operator_context.get("zone", "Kothrud") if operator_context else "Kothrud"
        operator_role = operator_context.get("role", "WardEngineer") if operator_context else "WardEngineer"

        trace_log = [
            f"Ingested SCADA packet for {transformer_id} in {transformer_zone} by {operator_role} ({operator_zone})",
            f"Telemetry: Depth={water_level_cm}cm, Leakage={neutral_amps}A, Voltage={phase_r_volts}V, Temp={oil_temp}°C"
        ]

        is_hazard = water_level_cm > 20.0 or neutral_amps > 40.0 or phase_r_volts < 50.0

        if not is_hazard:
            trace_log.append("Status: Nominal conditions. No safety action required.")
            return {
                "status": "HEALTHY",
                "cedarDecision": "NONE",
                "actions": [],
                "trace": trace_log
            }

        trace_log.append("HAZARD DETECTED: Evaluating Cedar policy against geographic tenant boundary...")

        cedar_check = evaluate_cedar_policy(
            action_name="TripFeederRelay",
            water_level_cm=water_level_cm,
            neutral_amps=neutral_amps,
            phase_r_volts=phase_r_volts,
            oil_temp=oil_temp,
            operator_zone=operator_zone,
            transformer_zone=transformer_zone,
            operator_role=operator_role
        )

        trace_log.append(f"Cedar Policy Decision: {cedar_check['decision']}")

        actions_taken = []
        if cedar_check["decision"] == "ALLOW":
            trip_result = simulate_feeder_isolation(
                transformer_id,
                f"Emergency trip: water depth {water_level_cm}cm exceeded 20cm limit under jurisdiction {operator_zone}."
            )
            actions_taken.append(trip_result)
            dispatch_result = generate_lineman_dispatch(
                transformer_id, 
                "MONSOON_INUNDATION_GROUND_FAULT", 
                ["IP68 Terminal Boot", "100A Fuse", "Silica Breather"]
            )
            actions_taken.append(dispatch_result)
            trace_log.append(f"Dispatched Lineman Ticket: {dispatch_result['ticketId']}")
        else:
            trace_log.append("BLOCKED: Cedar policy denied action. Invariant violation or cross-zone unauthorized access.")

        return {
            "status": "INCIDENT_RESOLVED" if cedar_check["decision"] == "ALLOW" else "INCIDENT_BLOCKED",
            "cedarDecision": cedar_check["decision"],
            "actions": actions_taken,
            "trace": trace_log
        }
