import sys
import os
import importlib.util
import pytest

# Directly load MonsoonChaosSimulator from disk
chaos_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "scripts", "chaos_sim.py"))
spec = importlib.util.spec_from_file_location("chaos_sim_module", chaos_path)
chaos_mod = importlib.util.module_from_spec(spec)
sys.modules["chaos_sim_module"] = chaos_mod
spec.loader.exec_module(chaos_mod)

MonsoonChaosSimulator = chaos_mod.MonsoonChaosSimulator


def test_monsoon_chaos_all_scenarios_pass():
    sim = MonsoonChaosSimulator()
    results = sim.run_all_scenarios()
    assert len(results) == 4
    for r in results:
        assert r["passed"] is True
