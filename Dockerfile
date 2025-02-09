FROM python:3.9-slim

WORKDIR /app

# System Dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    && rm -rf /var/lib/apt/lists/*

# Python Dependencies
COPY requirements.txt .
RUN pip3 install -r requirements.txt

# App Dateien
COPY *.py .
COPY .streamlit .streamlit/

# Port für Streamlit
EXPOSE 8501

# Health Check
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# Umgebungsvariablen
ENV STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0

# Start Command
CMD ["streamlit", "run", "app.py"]