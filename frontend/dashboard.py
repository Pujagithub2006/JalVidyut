import streamlit as st
import time
import sys
import os

agent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend", "agent"))
if agent_dir not in sys.path:
    sys.path.insert(0, agent_dir)

from agent import JalVidyutAgent
from execution.step_up_gate import step_up_gate

st.set_page_config(page_title="JalVidyut SCADA Control Plane", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    .main { background-color: #0b0f19; color: #f3f4f6; }
    .stMetric { background-color: #111827; padding: 12px; border-radius: 8px; border: 1px solid #1f2937; }
    .status-box { padding: 16px; border-radius: 8px; margin-bottom: 16px; font-weight: bold; }
    .status-healthy { background-color: #064e3b; border: 1px solid #059669; color: #6ee7b7; }
    .status-stepup { background-color: #78350f; border: 1px solid #d97706; color: #fde68a; }
    .status-tripped { background-color: #7f1d1d; border: 1px solid #dc2626; color: #fca5a5; }
</style>
""", unsafe_allow_html=True)

st.title("⚡ JalVidyut: Autonomous Monsoon Grid Safety Agent")
st.caption("Pune Municipal Distribution Network (11kV / 33kV) • AWS Cedar Bounded Authority Control Plane")

if "agent" not in st.session_state:
    st.session_state.agent = JalVidyutAgent()
if "last_result" not in st.session_state:
    st.session_state.last_result = None

st.sidebar.header("🕹️ SCADA Chaos Controls")
scenario = st.sidebar.selectbox(
    "Select Monsoon Scenario",
    [
        "1. Dry Nominal Conditions",
        "2. Debris Stuck-Float (Sensor Anomaly)",
        "3. Borderline Inundation (18cm Step-Up)",
        "4. Severe Deluge (28cm + 49A Lateral Shunt)"
    ]
)

telemetry = {
    "transformerId": "DP-PUNE-KOTHRUD-042",
    "zone": "Kothrud",
    "waterLevelCm": 4.0,
    "neutralCurrentAmps": 1.0,
    "voltageVolts": {"R": 230.0, "Y": 230.0, "B": 230.0},
    "oilTemperatureCelsius": 42.0
}

if scenario.startswith("2"):
    telemetry.update({"waterLevelCm": 24.0, "neutralCurrentAmps": 0.0, "oilTemperatureCelsius": 28.0})
elif scenario.startswith("3"):
    telemetry.update({"waterLevelCm": 18.0, "neutralCurrentAmps": 12.0})
elif scenario.startswith("4"):
    telemetry.update({"waterLevelCm": 28.5, "neutralCurrentAmps": 49.2, "voltageVolts": {"R": 210.0, "Y": 215.0, "B": 212.0}})

if st.sidebar.button("🚨 Inject SCADA Telemetry", use_container_width=True):
    st.session_state.last_result = st.session_state.agent.process_telemetry(
        telemetry, operator_context={"zone": "Kothrud", "role": "WardEngineer"}
    )

c1, c2, c3, c4 = st.columns(4)
c1.metric("Water Level", f"{telemetry['waterLevelCm']} cm", delta=f"{telemetry['waterLevelCm'] - 20.0:.1f} cm threshold")
c2.metric("Neutral Leakage", f"{telemetry['neutralCurrentAmps']} A", delta="Safety limit: 40A")
c3.metric("Phase R Voltage", f"{telemetry['voltageVolts']['R']} V")
c4.metric("Oil Temperature", f"{telemetry['oilTemperatureCelsius']} °C")

st.markdown("---")

col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("🌐 Grid Topology & Blast Perimeter")
    res = st.session_state.last_result
    
    if res:
        status = res["status"]
        if status == "HEALTHY":
            st.markdown('<div class="status-box status-healthy">✅ STATUS: GRID HEALTHY — All feeders energized</div>', unsafe_allow_html=True)
        elif status == "STEP_UP_REQUIRED":
            st.markdown('<div class="status-box status-stepup">⏳ STATUS: 60s OPERATOR STEP-UP GATE PENDING</div>', unsafe_allow_html=True)
            token = res.get("stepUpToken", {})
            st.warning(f"Token: {token.get('tokenId')}")
            col_b1, col_b2 = st.columns(2)
            if col_b1.button("✅ APPROVE MANUAL TRIP"):
                step_up_gate.resolve_token(token.get("tokenId"), approved=True)
                st.success("Operator Approved Feeder Isolation.")
            if col_b2.button("❌ REJECT"):
                step_up_gate.resolve_token(token.get("tokenId"), approved=False)
                st.error("Operator Rejected Request.")
        elif status == "INCIDENT_RESOLVED":
            st.markdown('<div class="status-box status-tripped">⚡ AUTONOMOUS ISOLATION ACTIVATED (AWS Cedar ALLOW)</div>', unsafe_allow_html=True)
            for a in res.get("actions", []):
                if "topologyPerimeter" in a:
                    p = a["topologyPerimeter"]
                    st.error(f"Quarantine Level: {p['isolationLevel']}")
                    st.write(f"Quarantined Circuits: `{p['quarantinedCircuits']}`")
                    st.info(f"Protected Critical Loads: `{p['protectedCriticalLoads']}`")
        elif status == "SENSOR_FAULT_HALTED":
            st.markdown('<div class="status-box status-tripped">⚠️ SENSOR FAULT DETECTED — Tripping Halted by Sentinel</div>', unsafe_allow_html=True)
            st.write(res.get("sentinelAudit", {}).get("flags"))
    else:
        st.info("Awaiting SCADA telemetry injection...")

with col_right:
    st.subheader("📜 Causal Decision Trace")
    if res and "trace" in res:
        for t in res["trace"]:
            st.code(t, language="log")
    else:
        st.write("No active trace logs.")
