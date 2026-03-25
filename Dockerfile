# Multi-stage build: Python backend + Node frontend
# --------------------------------------------------

# Stage 1: Build the React dashboard
FROM node:20-alpine AS frontend-build
WORKDIR /app/dashboard
COPY dashboard/package.json dashboard/package-lock.json ./
RUN npm ci --ignore-scripts
COPY dashboard/ ./
RUN npm run build

# Stage 2: Python backend
FROM python:3.11-slim AS backend
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
COPY --from=frontend-build /app/dashboard/dist /app/dashboard/dist

RUN mkdir -p /app/data /app/reports

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "mcp.server:app", "--host", "0.0.0.0", "--port", "8000"]
