import pika
import threading

def start_worker():
    def run():
        conn = pika.BlockingConnection(pika.ConnectionParameters("rabbitmq", 5672))
        ch = conn.channel()
        ch.queue_declare(queue="metrics_queue", durable=True)

        def callback(ch, method, props, body):
            print(f"Received: {body}")
            ch.basic_ack(method.delivery_tag)

        ch.basic_consume(queue="metrics_queue", on_message_callback=callback)
        print("Worker started...")
        ch.start_consuming()

    threading.Thread(target=run, daemon=True).start()
