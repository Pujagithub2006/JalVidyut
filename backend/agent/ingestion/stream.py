import json
import logging
import threading
from typing import Dict, Any, Callable
import paho.mqtt.client as mqtt

logger = logging.getLogger("JalVidyutStream")
logging.basicConfig(level=logging.INFO)

class TelemetryStreamIngestor:
    def __init__(self, broker_url: str = "broker.hivemq.com", port: int = 1883, topic: str = "jalvidyut/+/telemetry"):
        self.broker_url = broker_url
        self.port = port
        self.topic = topic
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.callbacks = []
        self.connected_event = threading.Event()
        self.subscribed_event = threading.Event()
        self._setup_handlers()

    def _setup_handlers(self):
        self.client.on_connect = self._on_connect
        self.client.on_subscribe = self._on_subscribe
        self.client.on_message = self._on_message

    def _on_connect(self, client, userdata, flags, reason_code, properties=None):
        logger.info(f"Connected to MQTT Broker: {self.broker_url} reason: {reason_code}")
        self.connected_event.set()
        self.client.subscribe(self.topic, qos=1)

    def _on_subscribe(self, client, userdata, mid, reason_code_list, properties=None):
        logger.info(f"Subscribed successfully to {self.topic}")
        self.subscribed_event.set()

    def _on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
            logger.info(f"Received live telemetry for DP: {payload.get('transformerId')}")
            for callback in self.callbacks:
                callback(payload)
        except Exception as e:
            logger.error(f"Failed to parse incoming MQTT packet: {e}")

    def register_callback(self, callback: Callable[[Dict[str, Any]], None]):
        self.callbacks.append(callback)

    def start(self, timeout: float = 10.0) -> bool:
        self.connected_event.clear()
        self.subscribed_event.clear()
        self.client.connect(self.broker_url, self.port, 60)
        self.client.loop_start()
        return self.subscribed_event.wait(timeout)

    def stop(self):
        self.client.loop_stop()
        self.client.disconnect()

stream_ingestor = TelemetryStreamIngestor()
