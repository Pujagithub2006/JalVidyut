from typing import Any, Dict, List, Optional
import time

class SensorAnomalySentinel:
    def __init__(self):
        # Cache previous readings for rate-of-change (jitter) analysis: {transformer_id: (timestamp, water_level_cm)}
        self._history: Dict[str, tuple[float, float]] = {}

    def audit_telemetry(self, telemetry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Audits physical sensor plausibility.
        Returns a dictionary with:
          - isValid: bool
          - flags: List[str]
          - recommendedAction: str ('PROCEED', 'DEGRADE_CONFIDENCE', 'HALT_EVALUATION')
        """
        flags: List[str] = []
        transformer_id = telemetry.get("transformerId", "UNKNOWN_DP")
        water_level = float(telemetry.get("waterLevelCm", 0.0))
        neutral_amps = float(telemetry.get("neutralCurrentAmps", 0.0))
        volts_r = float(telemetry.get("voltageVolts", {}).get("R", 230.0))
        oil_temp = float(telemetry.get("oilTemperatureCelsius", 45.0))
        now = time.time()

        # 1. Stuck-Float Anomaly: High water (>20cm) but completely zero leakage current and cold oil (<35°C)
        if water_level > 20.0 and neutral_amps == 0.0 and oil_temp < 35.0:
            flags.append("ANOMALY_STUCK_FLOAT_SUSPECTED")

        # 2. Severed CT Sensor Lead: Live energized phase (>= 200V) with submerged conditions (> 22cm),
        # but absolute zero ground current return (open secondary circuit)
        if volts_r >= 200.0 and water_level > 22.0 and neutral_amps == 0.0:
            flags.append("ANOMALY_SEVERED_CT_LEAD")

        # 3. Rate-of-Change / Sensor Jitter Breach (>15cm jump in <= 1.0 second)
        if transformer_id in self._history:
            prev_time, prev_water = self._history[transformer_id]
            time_delta = now - prev_time
            if time_delta <= 1.0 and abs(water_level - prev_water) > 15.0:
                flags.append("ANOMALY_WATER_LEVEL_RATE_BREACH")

        # Update cache
        self._history[transformer_id] = (now, water_level)

        is_valid = len(flags) == 0
        recommended_action = "PROCEED" if is_valid else "HALT_EVALUATION"

        return {
            "isValid": is_valid,
            "flags": flags,
            "recommendedAction": recommended_action,
            "auditedAt": now
        }

sensor_sentinel = SensorAnomalySentinel()
