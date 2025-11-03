# Discord Bot (Northflank)

## Env
- BOT_TOKEN (required)
- DB_PATH=/data/your_bot.db (recommended for SQLite persistence)

## Run locally
python -m pip install -r requirements.txt
cp .env.example .env
python bot.py

## Deploy (Northflank)
1) Create Project → Service (Worker) → Source: Git repo → Build: Dockerfile.
2) Secrets/Env: set BOT_TOKEN; set DB_PATH=/data/your_bot.db.
3) Storage: create Volume (e.g., bot-data) and mount at /data.
4) Deploy → check logs.
