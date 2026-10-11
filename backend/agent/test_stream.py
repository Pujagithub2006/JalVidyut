import json
import time
import pytest
import paho.mqtt.client as mqtt
import sys
import os
import threading

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from ingestion.stream import stream_ingestor

def test_mqtt_telemetry_flow():
    received = []
    received_event = threading.Event()

    def callback(data):
        received.append(data)
        if data.get("transformerId") == "DP-PUNE-TEST-LIVE-001":
            received_event.set()

    stream_ingestor.register_callback(callback)
    
    # 1. Connect and block until subscription is confirmed
    is_ready = stream_ingestor.start(timeout=10.0)
    assert is_ready, "Timed out waiting for MQTT broker connection and subscription ACK"

    # 2. Publish packet with QoS 1
    test_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    test_client.connect("broker.hivemq.com", 1883, 60)

    packet = {
        "transformerId": "DP-PUNE-TEST-LIVE-001",
        "waterLevelCm": 26.5,
        "neutralCurrentAmps": 42.0,
        "voltageVolts": {"R": 18.0, "Y": 220.0, "B": 218.0},
        "oilTemperatureCelsius": 52.0
    }

    inf = test_client.publish("jalvidyut/pune/telemetry", json.dumps(packet), qos=1)
    inf.wait_for_publish(timeout=5.0)
    test_client.disconnect()

    # 3. Wait up to 8s for subscriber event
    received_event.wait(timeout=8.0)
    stream_ingestor.stop()

    assert any(p.get("transformerId") == "DP-PUNE-TEST-LIVE-001" for p in received)
