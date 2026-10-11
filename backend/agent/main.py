from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agent import JalVidyutAgent

app = FastAPI(title="JalVidyut SCADA Control Plane")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

agent = JalVidyutAgent()

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
    return {"status": "ONLINE", "controlPlane": "JalVidyut-AWS-Cedar"}

@app.post("/api/telemetry/evaluate")
def evaluate(payload: TelemetryPayload):
    return agent.process_telemetry(payload.model_dump())
