# ─── Сборка образа NexusBot ────────────────────────────────────────────────────
FROM python:3.11-slim

# Метаданные
LABEL maintainer="KirillTomenko"
LABEL description="NexusBot — AI-консультант с персистентной памятью"

# Рабочая директория
WORKDIR /app

# Сначала копируем только зависимости — слой кешируется если requirements не менялся
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . .

# Создаём папку для SQLite-базы (volume монтируется сюда)
RUN mkdir -p data

# Порт не нужен — бот работает через polling, не HTTP
# Запуск
CMD ["python", "main.py"]
