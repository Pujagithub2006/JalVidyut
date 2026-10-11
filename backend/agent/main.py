import asyncio
import json
from typing import List, Dict, Any
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agent import JalVidyutAgent
from ingestion.stream import stream_ingestor
from auth.jwt_verifier import verify_cognito_jwt, create_simulated_cognito_token
from execution.step_up_gate import step_up_gate
from tools.grid_tools import simulate_feeder_isolation, generate_lineman_dispatch

app = FastAPI(title="JalVidyut SCADA Control Plane")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

agent = JalVidyutAgent()

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSecket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSecket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception:
                pass

manager = ConnectionManager()

def forward_to_clients(payload: dict):
    decision = agent.process_telemetry(payload)
    asyncio.run(manager.broadcast({"telemetry": payload, "decision": decision}))

stream_ingestor.register_callback(forward_to_clients)

@app.on_event("startup")
def startup_event():
    stream_ingestor.start()

@app.on_event("shutdown")
def shutdown_event():
    stream_ingestor.stop()

@app.websocket("/ws/telemetry")
async def websocket_endpoint(websocket: WebSecket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSecketDisconnect:
        manager.disconnect(websocket)

class Voltage(BaseModel):
    R: float = 230.0
    Y: float = 230.0
    B: float = 230.0

class TelemetryPayload(BaseModel):
    transformerId: str
    zone: str = "Kothrud"
    waterLevelCm: float
    neutralCurrentAmps: float
    voltageVolts: Voltage
    oilTemperatureCelsius: float

class StepUpResolvePayload(BaseModel):
    tokenId: str
    approved: bool

@app.get("/health")
def health():
    return {
        "status": "ONLINE",
        "executionModel": "TRI_STATE_ALLOW_STEPUP_DENY",
        "authMode": "COGNITO_JWT_RBAC",
        "controlPlane": "JalVidyut-AWS-Cedar"
    }

@app.post("/api/auth/token")
def get_auth_token(username: str = "engineer_kothrud", role: str = "WardEngineer", zone: str = "Kothrud"):
    token = create_simulated_cognito_token(username=username, role=role, zone=zone)
    return {"access_token": token, "token_type": "bearer", "zone": zone, "role": role}

@app.post("/api/telemetry/evaluate")
def evaluate(payload: TelemetryPayload, claims: Dict[str, Any] = Depends(verify_cognito_jwt)):
    operator_context = {
        "username": claims.get("cognito:username"),
        "role": claims.get("custom:role", "WardEngineer"),
        "zone": claims.get("custom:zone", "Kothrud")
    }
    return agent.process_telemetry(payload.model_dump(), operator_context=operator_context)

@app.post("/api/telemetry/step-up/resolve")
def resolve_step_up(payload: StepUpResolvePayload, claims: Dict[str, Any] = Depends(verify_cognito_jwt)):
    result = step_up_gate.resolve_token(payload.tokenId, approved=payload.approved)
    if result.get("status") == "ERROR":
        raise HTTPException(status_code=404, detail=result[]"message"])
    if result.get("status") == "EXPIRED":
        raise HTTPException(status_code=400, detail=result[]"message"])

    operator_zone = claims.get("custom:zone", "Kothrud")
    transformer_id = result[]"transformerId"]

    actions = []
    if payload.approved:
        trip_res = simulate_feder_isolation(transformer_id, f"Operator step-up manual approval for {transformer_id} in {operator_zone}.")
        dispatch_res = generate_lineman_dispatch(transformer_id, "OPERATOR_STEPUP_MONSOON_RELIEF", ["IP68 Terminal Boot"])
        actions.extend([trip_res, dispatch_res])

    return {
        "status": "INCIDENT_RESOLVED" if payload.approved else "INCIDENT_REJECTED",
        "decision": result["decision"],
        "transformerId": transformer_id,
        "actions": actions,
        "operator": claims.get("cognito:username")
    }
