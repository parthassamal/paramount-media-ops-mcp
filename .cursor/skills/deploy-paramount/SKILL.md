---
name: deploy-paramount
description: Deployment and setup guide for Paramount+ AI Operations platform. Use when setting up the project, deploying to production, or managing infrastructure.
---

# Deploy Paramount Platform Skill

Complete deployment and operations guide for Paramount+ AI Operations MCP.

## When to Use

Use this skill when:
- Setting up the project for first time
- Deploying to production
- Managing infrastructure
- Starting/stopping services
- Troubleshooting deployment issues
- Scaling the platform

## Quick Start (Development)

### 1. Clone and Setup
```bash
git clone https://github.com/parthassamal/paramount-media-ops-mcp.git
cd paramount-media-ops-mcp

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-ai.txt  # 40+ AI/ML libraries
```

### 2. Install AI Models
```bash
# Download models (~2.5GB, one-time)
./scripts/install_ai_models.sh

# This downloads:
# - spaCy en_core_web_sm
# - sentence-transformers all-MiniLM-L6-v2
# - HuggingFace CLIP ViT-B/32
# - OpenAI Whisper base
# - ChromaDB
# - NLTK data
```

### 3. Configure Environment
```bash
# Copy example config
cp config.example.py config.py

# Edit configuration (optional for mock mode)
nano config.py

# For production, set:
# - mock_mode = False
# - Configure JIRA, Confluence, NewRelic, Conviva credentials
```

### 4. Start Services
```bash
# Start everything (backend + frontend)
./start.sh

# Or start individually:
# Backend: uvicorn mcp.server:app --host 0.0.0.0 --port 8000 --reload
# Frontend: cd dashboard && npm run dev
```

### 5. Verify Deployment
```bash
# Check backend
curl http://localhost:8000/status

# Check AI services
curl http://localhost:8000/api/ai/health

# Check frontend
open http://localhost:5173
```

## Production Deployment

### Prerequisites
- Python 3.9+
- Node.js 18+
- 16GB RAM (for AI models)
- 10GB disk space (for models + data)
- Ubuntu 20.04+ / macOS 12+

### Option 1: Docker Deployment

**Create Dockerfile** (backend):
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt requirements-ai.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-ai.txt

# Copy application
COPY . .

# Download AI models
RUN chmod +x scripts/install_ai_models.sh
RUN ./scripts/install_ai_models.sh

# Expose port
EXPOSE 8000

# Run server
CMD ["uvicorn", "mcp.server:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Build and run**:
```bash
docker build -t paramount-ai-ops .
docker run -p 8000:8000 -e MOCK_MODE=false paramount-ai-ops
```

### Option 2: systemd Service (Linux)

**Create service file** (`/etc/systemd/system/paramount-ops.service`):
```ini
[Unit]
Description=Paramount AI Operations MCP Server
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/paramount-ops
Environment="PATH=/opt/paramount-ops/venv/bin"
ExecStart=/opt/paramount-ops/venv/bin/uvicorn mcp.server:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Enable and start**:
```bash
sudo systemctl daemon-reload
sudo systemctl enable paramount-ops
sudo systemctl start paramount-ops
sudo systemctl status paramount-ops
```

### Option 3: Cloud Deployment (AWS/GCP/Azure)

**AWS EC2**:
```bash
# Launch EC2 instance (t3.xlarge or larger)
# Ubuntu 20.04 LTS
# 16GB RAM, 50GB disk

# Install dependencies
sudo apt update
sudo apt install -y python3.11 python3.11-venv nginx

# Clone and setup
git clone https://github.com/parthassamal/paramount-media-ops-mcp.git
cd paramount-media-ops-mcp
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt -r requirements-ai.txt
./scripts/install_ai_models.sh

# Configure nginx reverse proxy
sudo nano /etc/nginx/sites-available/paramount-ops

# Start with systemd
sudo systemctl start paramount-ops
```

## Environment Variables

### Required for Production
```bash
export MOCK_MODE=false
export LOG_LEVEL=INFO
export LOG_FORMAT=json

# Atlassian
export JIRA_API_URL=https://your-domain.atlassian.net
export CONFLUENCE_API_URL=https://your-domain.atlassian.net
export ATLASSIAN_USERNAME=your-email@paramount.com
export ATLASSIAN_API_TOKEN=your-token

# Monitoring
export NEWRELIC_API_KEY=your-newrelic-key
export CONVIVA_API_KEY=your-conviva-key
export DYNATRACE_API_URL=your-dynatrace-url
export DYNATRACE_API_TOKEN=your-token

# Email
export EMAIL_IMAP_SERVER=imap.paramount.com
export EMAIL_USERNAME=ops-alerts@paramount.com
export EMAIL_PASSWORD=your-password

# AI Configuration
export AI_MODELS_CACHE_DIR=~/.cache/paramount-ai
export AI_EMBEDDINGS_MODEL=sentence-transformers/all-MiniLM-L6-v2
export AI_WHISPER_MODEL=base
```

## Scaling

### Horizontal Scaling

**Load balancer config** (nginx):
```nginx
upstream paramount_backend {
    least_conn;
    server 10.0.1.10:8000;
    server 10.0.1.11:8000;
    server 10.0.1.12:8000;
}

server {
    listen 80;
    server_name ops.paramount.com;
    
    location / {
        proxy_pass http://paramount_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Caching

Add Redis for caching:
```python
# In config.py
redis_url = "redis://localhost:6379"
cache_ttl = 300  # 5 minutes
```

### Database for ChromaDB

For production, use persistent ChromaDB:
```python
# In RAG engine initialization
persist_directory = "/data/chroma_db"  # Persistent volume
```

## Monitoring

### Health Checks
```bash
# Backend health
curl http://localhost:8000/status

# AI services health
curl http://localhost:8000/api/ai/health

# Individual service checks
curl http://localhost:8000/api/jira/health
```

### Logs
```bash
# View structured logs
tail -f logs/paramount_ops.log | jq

# Filter errors
tail -f logs/paramount_ops.log | jq 'select(.level == "error")'

# Monitor specific operation
tail -f logs/paramount_ops.log | jq 'select(.operation == "resolve_issue")'
```

### Metrics
```bash
# Check resource usage
htop

# Check disk usage
df -h

# Check model memory usage
nvidia-smi  # If using GPU
```

## Backup & Recovery

### Backup ChromaDB
```bash
# Backup vector database
tar -czf chroma_backup_$(date +%Y%m%d).tar.gz chroma_db/

# Backup to S3
aws s3 cp chroma_backup_$(date +%Y%m%d).tar.gz s3://paramount-backups/
```

### Restore ChromaDB
```bash
# Restore from backup
tar -xzf chroma_backup_20260129.tar.gz
```

## Troubleshooting

### Service Won't Start
```bash
# Check if port is in use
lsof -i :8000

# Check logs
tail -50 logs/paramount_ops.log

# Check Python environment
which python
python --version
pip list | grep -E "(fastapi|chromadb|transformers)"
```

### Models Not Loading
```bash
# Re-download models
./scripts/install_ai_models.sh

# Check model cache
ls -lh ~/.cache/huggingface/
ls -lh ~/.cache/torch/

# Test model loading
python -c "import spacy; spacy.load('en_core_web_sm')"
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
```

### High Memory Usage
```bash
# Check memory
free -h

# Reduce model size
# Use Whisper "tiny" instead of "base"
# Use smaller sentence-transformers model
# Enable model quantization
```

## Security Considerations

### API Authentication

Add authentication middleware:
```python
from fastapi import Security, HTTPException, status
from fastapi.security import HTTPBearer

security = HTTPBearer()

@app.middleware("http")
async def authenticate(request: Request, call_next):
    if request.url.path.startswith("/api/"):
        # Verify token
        token = request.headers.get("Authorization")
        if not verify_token(token):
            raise HTTPException(status_code=401)
    return await call_next(request)
```

### Rate Limiting

Add rate limiting:
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.get("/api/ai/rag/search")
@limiter.limit("100/minute")
async def search(request: Request):
    # ...
```

## Performance Optimization

### Enable GPU
```python
# In AI engine initialization
vision_engine = VisionEngine(enable_gpu=True)
voice_engine = VoiceEngine(enable_gpu=True)
```

### Batch Processing
```python
# Process multiple items at once
results = rag_engine.semantic_search_batch(queries, top_k=5)
```

### Model Quantization
```python
# Use quantized models for faster inference
model = SentenceTransformer('all-MiniLM-L6-v2')
model.half()  # FP16 precision
```

## References

- `start.sh` - Start all services
- `stop.sh` - Stop all services
- `status.sh` - Check service status
- `scripts/install_ai_models.sh` - Model installation
- `ERROR_HANDLING_SUMMARY.md` - Error handling guide
- `IMPLEMENTATION_COMPLETE.md` - Feature documentation
