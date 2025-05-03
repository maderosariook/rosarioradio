FROM python:3.9-slim-buster

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

RUN apt-get update && apt-get install -y ffmpeg libopus-dev libsodium-dev

COPY . .

CMD ["python", "rosarioradiourl.py"]
