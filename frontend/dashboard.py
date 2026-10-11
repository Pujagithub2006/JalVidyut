import streamlit as st
import requests

st.set_page_config(page_title="JalVidyut SCADA", layout="wide")

st.title("⚡ JalVidyut: Monsoon Inundation Control Plane")
st.write("Track 02: Heat and Water | Deterministic AWS Cedar Policy Engine")

col1, col2 = st.columns([1, 1.2])

with col1:
    st.subheader("1. Inundation & Telemetry Ingestion")
    preset = st.selectbox(
        "Incident Scenario Preset",
        [
            "Scenario A: Normal Monsoon Drizzle",
            "Scenario B: Street Flash Flood (Submerged DP)",
            "Scenario C: Post-Flood Overheated Reset"
        ]
    )

    if preset.startswith("Scenario A"):
        def_water, def_amps, def_volts, def_temp = 3.2, 1.4, 230.0, 48.0
    elif preset.startswith("Scenario B"):
        def_water, def_amps, def_volts, def_temp = 28.4, 46.1, 12.0, 54.0
    else:
        def_water, def_amps, def_volts, def_temp = 2.0, 0.5, 230.0, 78.0

    tf_id = st.text_input("Distribution Point ID", value="DP-PUNE-KOTHRUD-042")
    water = st.slider("Street Waterlogging Depth (cm)", 0.0, 60.0, float(def_water))
    amps = st.slider("Neutral Ground Leakage (A)", 0.0, 100.0, float(def_amps))
    volts = st.slider("Phase R Voltage (V)", 0.0, 250.0, float(def_volts))
    temp = st.slider("Transformer Oil Temp (°C)", 20.0, 100.0, float(def_temp))

    dispatch_btn = st.button("🚨 Dispatch Telemetry Packet", type="primary", use_container_width=True)

with col2:
    st.subheader("2. Evaluation & Decision Trace")
    if dispatch_btn:
        payload = {
            "transformerId": tf_id,
            "waterLevelCm": water,
            "neutralCurrentAmps": amps,
            "voltageVolts": {"R": volts, "Y": 218.0, "B": 221.0},
            "oilTemperatureCelsius": temp
        }
        try:
            res = requests.post("http://localhost:8000/api/telemetry/evaluate", json=payload, timeout=5)
            data = res.json()
            
            decision = data.get("cedarDecision", "NONE")
            if decision == "ALLOW":
                st.success("### Decision: ALLOW (Trip Authorized)")
            elif decision == "DENY":
                st.error("### Decision: DENY (Action Blocked)")
            else:
                st.info(f"### Status: {data.get('status', 'NOMINAL')}")

            st.write("#### Formal Verification Trace:")
            st.code("\n".join(data.get("trace", [])), language="bash")

            if data.get("actions"):
                st.write("#### Dispatched Grid Actions:")
                st.json(data["actions"])
        except Exception as e:
            st.error(f"Backend unreachable: {e}. Confirm Uvicorn is active on port 8000.")
    else:
        st.info("Select parameters and click 'Dispatch Telemetry Packet' to execute live triage.")
