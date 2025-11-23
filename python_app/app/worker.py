import pika
import threading
from metrics import sensor_value, humidity

def start_worker():
    def run():
        conn = pika.BlockingConnection(pika.ConnectionParameters("rabbitmq", 5672))
        ch = conn.channel()
        ch.queue_declare(queue="metrics_queue", durable=True)

        def callback(ch, method, props, body):
            msg = body.decode()
            # Парсимо повідомлення у форматі metric:value
            if ":" in msg:
                name, val = msg.split(":")
                val = float(val)
                if name == "sensor_value":
                    sensor_value.set(val)
                elif name == "humidity":
                    humidity.set(val)
            ch.basic_ack(delivery_tag=method.delivery_tag)
            print(f"Processed message: {msg}")

        ch.basic_consume(queue="metrics_queue", on_message_callback=callback)
        print("Worker started...")
        ch.start_consuming()

    threading.Thread(target=run, daemon=True).start()
