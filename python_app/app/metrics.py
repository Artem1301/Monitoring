import time
import random
import threading
import json
from prometheus_client import start_http_server, Gauge
from queue_utils import send_to_queue

METRICS_PORT = 8000
metrics_started = False

sensor_value_g = Gauge("sensor_value", "Random sensor value from Python app")
humidity_g = Gauge("humidity", "Random humidity value")

def generate_metrics():
    while True:
        sensor_val = random.randint(0, 100)
        humidity_val = random.randint(15, 75)

        # Прометеус метрики:
        sensor_value_g.set(sensor_val)
        humidity_g.set(humidity_val)

        # Надсилання RabbitMQ:
        send_to_queue(json.dumps({
            "type": "metric",
            "sensor_value": sensor_val,
            "humidity": humidity_val,
            "timestamp": time.time()
        }))

        time.sleep(5)


def start_metrics_server_once():
    global metrics_started
    if not metrics_started:
        start_http_server(METRICS_PORT)
        threading.Thread(target=generate_metrics, daemon=True).start()
        metrics_started = True
        print(f"Prometheus metrics server started on port {METRICS_PORT}")
