import pika
import time

def send_to_queue(message, max_retries=5, retry_delay=3):
    retries = 0

    while retries < max_retries:
        try:
            conn = pika.BlockingConnection(pika.ConnectionParameters("rabbitmq", 5672))
            ch = conn.channel()
            ch.queue_declare(queue="metrics_queue", durable=True)

            ch.basic_publish(
                exchange="",
                routing_key="metrics_queue",
                body=message,
                properties=pika.BasicProperties(delivery_mode=2)
            )
            conn.close()
            print(f"[send_to_queue] Message sent: {message}")
            return True

        except pika.exceptions.AMQPConnectionError:
            retries += 1
            print(f"Retry {retries}/{max_retries}...")
            time.sleep(retry_delay)

    print(f"Failed to send message: {message}")
    return False
