from typing import Any, Dict, List, Set

class PuneGridTopology:
    def __init__(self):
        # Ring-main topology map for Pune distribution zones
        # Node format: (FeederID, [Subordinate Transformers], [Lateral Interconnects])
        self.feeder_hierarchy: Dict[str, Dict[str, Any]] = {
            "DP-PUNE-KOTHRUD-042": {
                "substation": "SUB-PUNE-WEST-33KV",
                "upstreamFeeder": "FDR-KOTHRUD-11KV-04",
                "lateralTransformers": ["DP-PUNE-KOTHRUD-041", "DP-PUNE-KOTHRUD-043"],
                "criticalLoads": ["Kothrud Metro Feeder", "Sahyadri Hospital Ring"]
            },
            "DP-PUNE-SHIVAJINAGAR-012": {
                "substation": "SUB-PUNE-CENTRAL-33KV",
                "upstreamFeeder": "FDR-SHIVAJI-11KV-01",
                "lateralTransformers": ["DP-PUNE-SHIVAJINAGAR-011"],
                "criticalLoads": ["District Court Line"]
            }
        }

    def compute_quarantine_perimeter(
        self,
        transformer_id: str,
        neutral_leakage_amps: float
    ) -> Dict[str, Any]:
        """
        Determines the safe isolation perimeter.
        If neutral leakage is extreme (>45A), back-feed risk requires lateral ring isolation.
        Otherwise, only the local breaker is isolated to avoid unnecessary blackouts.
        """
        node = self.feeder_hierarchy.get(transformer_id)
        if not node:
            return {
                "transformerId": transformer_id,
                "isolationLevel": "LOCAL_ONLY",
                "quarantinedCircuits": [transformer_id],
                "protectedCriticalLoads": []
            }

        quarantined: List[str] = [transformer_id]
        level = "LOCAL_ONLY"

        # If ground leakage is severe, lateral inter-ties carry reverse shock danger
        if neutral_leakage_amps > 45.0:
            level = "LATERAL_RING_SHUNT"
            quarantined.extend(node["lateralTransformers"])

        return {
            "transformerId": transformer_id,
            "isolationLevel": level,
            "upstreamFeeder": node["upstreamFeeder"],
            "quarantinedCircuits": quarantined,
            "protectedCriticalLoads": node["criticalLoads"]
        }

grid_topology = PuneGridTopology()
