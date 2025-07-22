FROM python:3.11-slim

WORKDIR /app

COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend/server_dm_polls.py ./backend/server_dm_polls.py

EXPOSE 8000

CMD ["uvicorn", "backend.server_dm_polls:app", "--host", "0.0.0.0", "--port", "8000"] 