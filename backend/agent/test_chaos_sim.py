import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from scripts.chaos_sim import MonsoonChaosSimulator

def test_monsoon_chaos_all_scenarios_pass():
    sim = MonsoonChaosSimulator()
    results = sim.run_all_scenarios()
    assert len(results) == 4
    for r in results:
        assert r["passed"] is True
