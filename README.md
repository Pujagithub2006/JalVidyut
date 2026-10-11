# JalVidyut (⚡)

> **Autonomous Monsoon Inundation & Submerged Transformer Safety Control Plane**  
> Built for AWS Bharat Builds Tour — Event 02: Environmental Hacks (Track 02: Heat and Water).

## Overview
During severe Indian monsoon downpours, street waterlogging submerges roadside distribution transformers (DP boxes). High-voltage ground current leaks into standing floodwater, creating life-threatening electrocution hazards for pedestrians before melting internal coils.

**JalVidyut** bridges the gap between probabilistic AI pattern triage and physical grid safety:
1. Senses immersion depth, ground leakage, and phase metrics.
2. The **Strands Agent** classifies the fault.
3. The **AWS Cedar Policy Engine** deterministically authorizes circuit isolation before power is cut..

## Architecture

[ Telemetry Ingestion ] ──> [ Strands Agent Loop ] ──> [ AWS Cedar Engine ] ──> [ Breaker Tripped + Lineman Ticket ]

## Running Locally (Build It Track)
1. Install dependencies:
   ```bash
   pip install -r backend/agent/requirements.txt
   ```

2. Run safety invariant tests:
   ```bash
   pytest backend/agent/test_policies.py -v
   ```

3. Run the backend service:
   ```bash
   uvicorn backend.agent.main:app --reload --port 8000
   ```

4. Run the frontend console:
   ```bash
   streamlit run frontend/dashboard.py
   ```

---

### Verification and Execution Sequence

1. **Verify Invariants:** Run `pytest backend/agent/test_policies.py -v` (expect all 4 tests to pass green).
2. **Start Backend:** Run `uvicorn main:app --reload --port 8000` from `backend/agent`.
3. **Start Dashboard:** Run `streamlit run frontend/dashboard.py`.
4. **Inspect:** Test Scenario A (nominal) vs. Scenario B (flood immersion triggering Cedar `ALLOW`).