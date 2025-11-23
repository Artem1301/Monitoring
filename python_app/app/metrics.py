import random
import time
import threading
from prometheus_client import Gauge, start_http_server
from mq import send_to_queue

METRICS_PORT = 8000
metrics_started = False

sensor_value = Gauge("sensor_value", "Random sensor value from Python app")
humidity = Gauge("humidity", "Random humidity value")

def generate_metrics():
    while True:
        val = random.randint(0, 100)
        hum = random.randint(15, 75)

        # Відправляємо в чергу
        send_to_queue(f"sensor_value:{val}")
        send_to_queue(f"humidity:{hum}")

        time.sleep(5)

def start_metrics_server_once():
    global metrics_started
    if not metrics_started:
        start_http_server(METRICS_PORT)
        threading.Thread(target=generate_metrics, daemon=True).start()
        metrics_started = True
        print(f"Prometheus metrics server started on port {METRICS_PORT}")
