from tools.grid_tools import (
    evaluate_cedar_policy,
    simulate_feeder_isolation,
    generate_lineman_dispatch,
)
from intelligence.bedrock_risk import bedrock_scorer
from execution.step_up_gate import step_up_gate

class JalVidyutAgent:
    def __init__(self):
        self.system_prompt = "JalVidyut autonomous monsoon flood safety agent."

    def process_telemetry(self, telemetry: dict, operator_context: dict = None, geo_context: dict = None) -> dict:
        transformer_id = telemetry.get("transformerId", "DP-PUNE-KOTHRUD-042")
        transformer_zone = telemetry.get("zone", "Kothrud")
        water_level_cm = telemetry.get("waterLevelCm", 0.0)
        neutral_amps = telemetry.get("neutralCurrentAmps", 0.0)
        phase_r_volts = telemetry.get("voltageVolts", {}).get("R", 230.0)
        oil_temp = telemetry.get("oilTemperatureCelsius", 45.0)

        operator_zone = operator_context.get("zone", "Kothrud") if operator_context else "Kothrud"
        operator_role = operator_context.get("role", "WardEngineer") if operator_context else "WardEngineer"

        bedrock_eval = bedrock_scorer.calculate_surge_risk(telemetry, geographical_context=geo_context)
        surge_risk = bedrock_eval["mlFloodSurgeRisk"]

        trace_log = [
            f"SCADA: {transformer_id} in {transformer_zone} via {operator_role} ({operator_zone})",
            f"Sensors: Water={water_level_cm}cm, Leakage={neutral_amps}A, Volts={phase_r_volts}V, Temp={oil_temp}C",
            f"Surge Risk: {surge_risk*100:.1f}% - {bedrock_eval['reasoning']}"
        ]

        is_borderline = (16.0 <= water_level_cm <= 20.0) and (neutral_amps <= 40.0) and (surge_risk < 0.80)
        if is_borderline:
            token = step_up_gate.create_step_up_token(transformer_id, water_level_cm, transformer_zone)
            trace_log.append(f"STEP-UP REQUIRED: Borderline flood ({water_level_cm}cm). 60s human gate: {token['tokenId']}")
            return {
                "status": "STEP_UP_REQUIRED",
                "cedarDecision": "STEP_UP",
                "stepUpToken": token,
                "bedrockRisk": bedrock_eval,
                "actions": [],
                "trace": trace_log
            }

        is_hazard = (
            water_level_cm > 20.0 or 
            neutral_amps > 40.0 or 
            phase_r_volts < 50.0 or 
            (water_level_cm > 12.0 and surge_risk > 0.80)
        )

        if not is_hazard:
            trace_log.append("Status: Nominal conditions. Safety bounds not breached.")
            return {
                "status": "HEALTHY",
                "cedarDecision": "NONE",
                "bedrockRisk": bedrock_eval,
                "actions": [],
                "trace": trace_log
            }

        cedar_check = evaluate_cedar_policy(
            action_name="TripFeederRelay",
            water_level_cm=water_level_cm,
            neutral_amps=neutral_amps,
            phase_r_volts=phase_r_volts,
            oil_temp=oil_temp,
            operator_zone=operator_zone,
            transformer_zone=transformer_zone,
            operator_role=operator_role,
            ml_flood_surge_risk=surge_risk
        )

        trace_log.append(f"Cedar Policy Decision: {cedar_check['decision']}")

        actions_taken = []
        if cedar_check["decision"] == "ALLOW":
            trip_result = simulate_feeder_isolation(
                transformer_id,
                f"Automated trip: depth {water_level_cm}cm exceeds bounds under way for {operator_zone}."
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
            trace_log.append("BLOCKED: Cedar denied action.")

        return {
            "status": "INCIDENT_RESOLVED" if cedar_check["decision"] == "ALLOW" else "INCIDENT_BLOCKED",
            "cedarDecision": cedar_check["decision"],
            "bedrockRisk": bedrock_eval,
            "actions": actions_taken,
            "trace": trace_log
        }
