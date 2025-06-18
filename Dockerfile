FROM python:3.10-slim

RUN apt-get update && \
    apt-get install -y ffmpeg libsndfile1 git && \
    apt-get clean

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir git+https://github.com/openai/whisper.git \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
