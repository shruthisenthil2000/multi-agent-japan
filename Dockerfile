# Voice Travel Copilot — Streamlit UI
FROM python:3.11-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -e ".[voice]"

EXPOSE 8501

CMD ["streamlit", "run", "app/voice_agent.py", "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true"]
