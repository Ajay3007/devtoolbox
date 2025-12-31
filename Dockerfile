FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Backend setup
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# Frontend setup
COPY frontend/package.json ./frontend/package.json
COPY frontend/package-lock.json ./frontend/package-lock.json
RUN cd frontend && npm ci

# Copy application code
COPY backend ./backend
COPY frontend ./frontend
COPY docs ./docs

EXPOSE 5000 8080

# Start both services
CMD bash -c "python backend/app.py & cd frontend && npm run dev"
