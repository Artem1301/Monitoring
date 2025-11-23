import time
import random
import threading
from prometheus_client import start_http_server, Gauge

METRICS_PORT = 8000
metrics_started = False
sensor_value = Gauge("sensor_value", "Random sensor value from Python app")
humidity = Gauge("humidity", "Random humidity value")

def generate_metrics():
    while True:
        sensor_value.set(random.randint(0, 100))
        humidity.set(random.randint(15, 75))
        time.sleep(5)

def start_metrics_server_once():
    global metrics_started
    if not metrics_started:
        start_http_server(METRICS_PORT)
        threading.Thread(target=generate_metrics, daemon=True).start()
        metrics_started = True
        print(f"Prometheus metrics server started on port {METRICS_PORT}")
