import json
from typing import List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agent import JalVidyutAgent
from ingestion.stream import stream_ingestor

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

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception:
                pass

manager = ConnectionManager()

def forward_to_clients(payload: dict):
    # Process through agent and broadcast real-time state
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
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

class Voltage(BaseModel):
    R: float = 230.0
    Y: float = 230.0
    B: float = 230.0

class TelemetryPayload(BaseModel):
    transformerId: str
    waterLevelCm: float
    neutralCurrentAmps: float
    voltageVolts: Voltage
    oilTemperatureCelsius: float

@app.get("/health")
def health():
    return {"status": "ONLINE", "streamEngine": "ACTIVE", "controlPlane": "JalVidyut-AWS-Cedar"}

@app.post("/api/telemetry/evaluate")
def evaluate(payload: TelemetryPayload):
    return agent.process_telemetry(payload.model_dump())
