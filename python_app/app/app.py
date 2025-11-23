from flask import Flask
from database import init_db, close_db
from auth import auth_bp
from worker import start_worker
from metrics import start_metrics_server_once

app = Flask(__name__)
app.teardown_appcontext(close_db)
app.register_blueprint(auth_bp)

if __name__ == "__main__":
    init_db()
    start_worker()              # запускаємо worker
    start_metrics_server_once() # запускаємо генератор метрик та Prometheus server
    app.run(host="0.0.0.0", port=5000, debug=False)
