# ⚡ JalVidyut: Autonomous Monsoon Grid Safety Agent
### Bounded-Authority SCADA Protection for Pune's 11kV/33kV Distribution Grid

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://jalvidyut.streamlit.app)
[![AWS Bedrock](https://img.shields.io/badge/AWS%20Bedrock-Claude%203%20Haiku-FF9900?logo=amazon-aws)](https://aws.amazon.com/bedrock/)
[![AWS Cedar](https://img.shields.io/badge/Policy%20Engine-AWS%20Cedar-232F3E?logo=amazon-aws)](https://www.cedarpolicy.com/)
[![Tests](https://img.shields.io/badge/Tests-25%2F25%20Passing-brightgreen)](tests/)
[![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)](https://python.org)

---

#  The Problem: Monsoon Electrocution vs. Uncontrolled LLM Trips

During intense Western Ghats monsoon downpours, low-lying distribution substations across Pune (e.g., Kothrud Ward, Deccan Gymkhana, Mutha riverbank) face rapid flood inundation. Pad-mounted 11kV/33kV transformers submerged in stormwater turn surrounding water bodies into live electrical hazards, presenting fatal public electrocution risks.

## The Engineering Dilemma

1. **Human Operator Latency**
   - Flash floods escalate within minutes.
   - Manual inspection and dispatch often require **45–90 minutes** through traffic.

2. **Traditional SCADA Limitations**
   - Conventional protection relays trip **only after** overcurrent or short-circuit faults.
   - They cannot proactively isolate transformers before dangerous water ingress.

3. **The LLM Hallucination Hazard**
   - Generative AI is probabilistic.
   - Giving an unconstrained LLM authority to operate high-voltage switchgear introduces an unacceptable risk of unnecessary feeder trips, potentially disconnecting hospitals, metro systems, and emergency infrastructure.

---

#  JalVidyut Solution: Bounded Authority Architecture

JalVidyut separates **Hydrological Risk Intelligence** from **Safety-Critical Trip Authority**.

```text
                     SCADA IoT Ingestion
     (Water Level • Neutral Leakage • Voltages • Oil Temp)
                              │
                              ▼
                 Pre-Authorization Sentinel
          ─────── Hardware anomaly? ───────
              │                         │
              ▼                         ▼
      Reject + Raise Ticket         Sensor Valid
                                        │
               ┌────────────────────────┴─────────────────────────┐
               ▼                                                  ▼
     Amazon Bedrock Agent                            AWS Cedar Policy Engine
 (Claude 3 Haiku Flood Reasoning)              (Deterministic Safety Invariants)
               │                                                  │
               └───────────────────────┬──────────────────────────┘
                                       ▼
                           Bounded Authority Gate
                                       │
                  ┌────────────────────┴─────────────────────┐
                  ▼                                          ▼
     Topological Quarantine Engine               Human-in-the-Loop Gate
 (Ring Shunt + Feeder Isolation)             (SNS Alert + 60s Confirmation)
```

---

#  System Workflow

### 1. Pre-Authorization Sentinel

Before any AI reasoning occurs, sensor values are validated against physical constraints.

Examples:

- Float sensor indicates flooding while neutral leakage remains zero.
- Sudden impossible voltage jumps.
- Frozen water-level readings despite changing rainfall.

Invalid telemetry is discarded and converted into a maintenance ticket instead of influencing operational decisions.

---

### 2. Amazon Bedrock (Claude 3 Haiku)

The Bedrock agent performs contextual environmental reasoning using:

- Flood progression
- Rainfall intensity
- Water-level trends
- Ward elevation
- Historical flood patterns

It predicts the likelihood that a transformer will become hazardous in the immediate future.

Importantly:

> **Bedrock never receives authority to trip electrical infrastructure.**

Its role is strictly advisory.

---

### 3. AWS Cedar Policy Engine

Every proposed action is evaluated against deterministic Cedar policies.

Examples of enforced rules:

- Never disconnect protected hospital feeders.
- Never trip a breaker without confirmed flooding.
- Reject AI recommendations violating electrical safety constraints.
- Require human approval for medium-risk situations.

Cedar acts as the mathematical safety firewall between AI recommendations and physical infrastructure.

---

### 4. Topological Quarantine Engine

Instead of disconnecting an entire substation, JalVidyut computes alternative feeder paths.

Capabilities include:

- Ring-main isolation
- Feeder shunting
- Hazard containment
- Maintaining power to hospitals and metro stations whenever alternate topology exists

This minimizes customer outages while maximizing public safety.

---

### 5. Human-in-the-Loop Gate

Borderline scenarios require operator confirmation.

Workflow:

- Amazon SNS sends an emergency notification.
- Decision metadata is stored in DynamoDB.
- Engineers receive a **60-second confirmation window**.
- If approved, the policy engine authorizes execution.

This ensures uncertain situations always include human oversight.

---

#  Tech Stack

| Domain | Technology | Purpose |
|---------|------------|---------|
| **GenAI Reasoning** | Amazon Bedrock (Claude 3 Haiku) | Flood risk analysis and contextual reasoning |
| **Policy Enforcement** | AWS Cedar (`cedarpy`) | Deterministic authorization of control actions |
| **Notifications** | Amazon SNS | Human approval workflow |
| **Audit Logging** | Amazon DynamoDB | Incident history and operator decisions |
| **Dashboard** | Streamlit | Industrial SCADA digital twin |
| **Language** | Python 3.12 | Backend services |
| **Testing** | Pytest | Safety verification |

---

#  Safety Philosophy

The architecture intentionally prevents AI from directly controlling critical electrical infrastructure.

Instead:

```
AI
 ↓
Recommendation

 ↓

Cedar Policies

 ↓

Safety Verification

 ↓

Approved Action

 ↓

SCADA
```

The AI provides intelligence.

The policy engine provides authority.

This separation eliminates an entire class of LLM hallucination failures.

---

#  Test Suite (100% Pass Rate)

The project contains a comprehensive automated verification suite.

| Test File | Purpose |
|-----------|---------|
| `tests/test_policies.py` | Cedar authorization invariants |
| `tests/test_sentinel.py` | Hardware anomaly detection |
| `tests/test_quarantine.py` | Ring topology and feeder isolation |
| `tests/test_hitl.py` | Human approval workflow |

Run locally:

```bash
pytest -v
```

Example output:

```text
=============================
25 passed in 0.42s
=============================
```

---

#  Running Locally

## 1. Clone Repository

```bash
git clone https://github.com/Pujagithub2006/JalVidyut.git
cd JalVidyut
```

---

## 2. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 3. Configure AWS Credentials (Optional)

```bash
export AWS_DEFAULT_REGION="ap-southeast-2"
export AWS_ACCESS_KEY_ID="your_access_key"
export AWS_SECRET_ACCESS_KEY="your_secret_key"
```

If credentials are unavailable, the platform automatically switches to local simulation mode.

---

## 4. Launch Dashboard

```bash
streamlit run frontend/dashboard.py
```

---

#  Project Highlights

- Autonomous flood-risk reasoning using Amazon Bedrock
- Deterministic authorization with AWS Cedar
- Hardware telemetry sanity validation
- Human approval workflow with Amazon SNS
- Immutable incident logging via DynamoDB
- SCADA Digital Twin built in Streamlit
- Comprehensive automated testing
- Safety-first bounded AI architecture

---

#  Hackathon Information

**Hackathon**

Amazon Bharat Builds (ABB) 2026

**Developer**

Puja Nikam

---

#  License

This project is intended for educational, research, and hackathon demonstration purposes. It illustrates a bounded-authority architecture for integrating Generative AI into safety-critical SCADA environments while ensuring deterministic operational safeguards.