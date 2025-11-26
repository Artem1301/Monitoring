import pika
import json
import psycopg2
from datetime import datetime
import threading


DB_HOST = "postgres"
DB_NAME = "sensors_db"
DB_USER = "postgres"
DB_PASSWORD = "postgres"


def save_login_event(event):
    conn = psycopg2.connect(
        host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD
    )
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO login_events (username, event_time)
        VALUES (%s, to_timestamp(%s))
    """, (
        event["username"],
        event["timestamp"]
    ))

    conn.commit()
    cur.close()
    conn.close()


def save_sensor_metric(event):
    conn = psycopg2.connect(
        host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD
    )
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO sensor_metrics (sensor_value, humidity, event_time)
        VALUES (%s, %s, to_timestamp(%s))
    """, (
        event["sensor_value"],
        event["humidity"],
        event["timestamp"]
    ))

    conn.commit()
    cur.close()
    conn.close()


def start_worker():
    def run():
        conn = pika.BlockingConnection(pika.ConnectionParameters("rabbitmq", 5672))
        ch = conn.channel()
        ch.queue_declare(queue="metrics_queue", durable=True)

        print("Worker listening for RabbitMQ messages...")

        def callback(ch, method, props, body):
            print(f"Worker received: {body}")

            try:
                data = json.loads(body.decode())
            except Exception as e:
                print("Invalid JSON:", e)
                ch.basic_ack(method.delivery_tag)
                return

            msg_type = data.get("type")

            if msg_type == "login_event":
                save_login_event(data)
                print("Saved login event.")

            elif msg_type == "metric":
                save_sensor_metric(data)
                print("Saved metric.")

            else:
                print("Unknown message type:", msg_type)

            ch.basic_ack(method.delivery_tag)

        ch.basic_consume(queue="metrics_queue", on_message_callback=callback)
        ch.start_consuming()

    threading.Thread(target=run, daemon=True).start()
