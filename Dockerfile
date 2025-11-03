FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates tzdata && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# persistent data goes here (mount a Northflank Volume to /data)
RUN mkdir -p /data

# change bot.py → bot_slash.py if that's your entry
CMD ["python", "-u", "bot.py"]
