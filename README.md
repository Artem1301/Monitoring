# Sensor Monitoring System  
Повноцінна система моніторингу сенсорів у реальному часі з використанням:

- **Python FastAPI** — API авторизації  
- **Worker (Python)** — отримання даних з RabbitMQ  
- **RabbitMQ** — черга повідомлень  
- **PostgreSQL** — база для збереження показників  
- **Prometheus** — збір метрик  
- **Grafana** — візуалізація даних  
- **Docker Compose** — запуск усієї системи

Як запустити:

```bash
git clone https://github.com/Artem1301/Monitoring
cd Monitoring
docker-compose up --build
```

Postman
```bash
http://localhost:5000/register
```
```bash
{
  "username": "your username",
  "password": "your password"
}
```

```bash
http://localhost:5000/login
```
```bash
{
  "username": "your username",
  "password": "your password"
}
```
Після логіну запускається генерація метрик.

Що зупинити систему:
```bash
docker-compose down 
```
