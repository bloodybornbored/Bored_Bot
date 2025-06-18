# Используем официальный python-образ с 3.10
FROM python:3.10-slim

# Устанавливаем ffmpeg и системные зависимости
RUN apt-get update && \
    apt-get install -y ffmpeg libsndfile1 git && \
    apt-get clean

# Указываем рабочую директорию
WORKDIR /app

# Копируем зависимости
COPY requirements.txt .

# Устанавливаем зависимости, включая whisper с GitHub
RUN pip install --no-cache-dir git+https://github.com/openai/whisper.git \
    && pip install --no-cache-dir -r requirements.txt

# Копируем всё приложение
COPY . .

# Запуск бота
CMD ["python", "main.py"]
