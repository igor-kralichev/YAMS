# run_all.py
import subprocess
import time


services = [
    {"name": "auth_service", "port": 8001},
    {"name": "deal_service", "port": 8002},
    {"name": "rating_service", "port": 8003},
    {"name": "admin_service", "port": 8005},
    {"name": "api_gateway", "port": 8000}
]

processes = []

for service in services:
    cmd = f"uvicorn {service['name']}.app.main:app --port {service['port']}"
    p = subprocess.Popen(cmd, shell=True)
    processes.append(p)
    time.sleep(2)  # Пауза для инициализации сервиса
    print(f"Сервис {service['name']} запущен на порту {service['port']}")

print("\nВсе сервисы запущены!")
print("Нажмите Ctrl+C для остановки\n")


try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    for p in processes:
        p.terminate()
    print("\nВсе сервисы остановлены")