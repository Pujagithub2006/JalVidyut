import json
from tools.grid_tools import (
    evaluate_cedar_policy,
    simulate_feeder_isolation,
    generate_lineman_dispatch,
)
from intelligence.bedrock_risk import bedrock_scorer
from execution.step_up_gate import step_up_gate
from notifications.sns_dispatcher import sns_dispatcher


class JalVidyutAgent:
    def __init__(self):
        self.system_prompt = (
            "JalVidyut autonomous monsoon flood and transformer safety agent. "
            "Evaluates Cedar policies before tripping relays and dispatches emergency crews."
        )

    def process_telemetry(
        self,
        telemetry: dict,
        operator_context: dict = None,
        geo_context: dict = None
    ) -> dict:
        transformer_id = telemetry.get("transformerId", "UNKNOWN_DP")
        transformer_zone = telemetry.get("zone", "Kothrud")
        water_level_cm = float(telemetry.get("waterLevelCm", 0.0))
        neutral_amps = float(telemetry.get("neutralCurrentAmps", 0.0))
        phase_r_volts = float(telemetry.get("voltageVolts", {}).get("R", 230.0))
        oil_temp = float(telemetry.get("oilTemperatureCelsius", 45.0))

        operator_zone = operator_context.get("zone", "Kothrud") if operator_context else "Kothrud"
        operator_role = operator_context.get("role", "WardEngineer") if operator_context else "WardEngineer"

        # 1. Real-time Bedrock Hydrological Risk Assessment
        bedrock_eval = bedrock_scorer.calculate_surge_risk(telemetry, geographical_context=geo_context)
        surge_risk = bedrock_eval.get("mlFloodSurgeRisk", 0.0)

        trace_log = [
            f"SCADA Telemetry for {transformer_id} in {transformer_zone} by {operator_role} ({operator_zone})",
            f"Sensors: FloodWater={water_level_cm}cm, Neutral={neutral_amps}A, PhaseR={phase_r_volts}V, Temp={oil_temp}C",
            f"Bedrock Surge Risk: {round(surge_risk * 100, 1)}% - {bedrock_eval.get('reasoning', 'Nominal')}"
        ]

        # 2. Step-Up Boundary Check: Borderline flood (16cm - 20cm) without catastrophic current leakage
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
                "trace": trace_log,
            }

        # 3. Hazard Threshold Check
        is_hazard = (
            water_level_cm > 20.0
            or neutral_amps > 40.0
            or phase_r_volts < 50.0
            or (water_level_cm > 12.0 and surge_risk > 0.80)
        )

        if not is_hazard:
            trace_log.append("Status: DP nominal and within dry limits. No safety trip authorized.")
            return {
                "status": "HEALTHY",
                "cedarDecision": "NONE",
                "bedrockRisk": bedrock_eval,
                "actions": [],
                "trace": trace_log,
            }

        trace_log.append("CRITICAL: Safety invariants breached. Evaluating AWS Cedar Policy...")

        # 4. Deterministic Cedar Evaluation
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
        trace_log.append(f"Cedar Policy Decision: {cedar_check['decision']} (Reasons: {cedar_check.get('reasons', [])})")

        actions_taken = []
        if cedar_check["decision"] == "ALLOW":
            trip_result = simulate_feeder_isolation(
                transformer_id,
                f"Emergency autonomous trip: water level at {water_level_cm}cm exceeded safety boundary for {operator_zone}."
            )
            actions_taken.append(trip_result)

            parts = [
                "IP68 Waterproof Terminal Boot",
                "100A Horn-Gap Fuse Kit",
                "Silica Gel Dehydrating Breather",
            ]
            dispatch_result = generate_lineman_dispatch(
                transformer_id,
                "MONSOON_INUNDATION_GROUND_FAULT",
                parts
            )
            actions_taken.append(dispatch_result)
            trace_log.append(f"Dispatched Lineman work order: {dispatch_result['ticketId']}")

            # 5. Amazon SNS Notifications Dispatch
            sms_res = sns_dispatcher.dispatch_lineman_sms(
                phone_number="+919876543210",
                ticket_id=dispatch_result["ticketId"],
                transformer_id=transformer_id,
                zone=transformer_zone,
                parts=parts
            )
            actions_taken.append({"sms_notification": sms_res})

            ward_res = sns_dispatcher.broadcast_public_ward_alert(
                zone=transformer_zone,
                transformer_id=transformer_id,
                reason=f"Water level reached {water_level_cm}cm with leakage {neutral_amps}A."
            )
            actions_taken.append({"ward_broadcast": ward_res})
            trace_log.append("Dispatched Amazon SNS SMS work orders and Ward emergency alerts.")
        else:
            trace_log.append("BLOCKED: Cedar policy denied relay isolation.")

        return {
            "status": "INCIDENT_RESOLVED" if cedar_check["decision"] == "ALLOW" else "INCIDENT_BLOCKED",
            "cedarDecision": cedar_check["decision"],
            "bedrockRisk": bedrock_eval,
            "actions": actions_taken,
            "trace": trace_log,
        }
