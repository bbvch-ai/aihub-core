# Docling Granite Deployment

Production-ready deployment of IBM Granite Docling model with LiteLLM API gateway, Docling Serve document processing, and Traefik reverse proxy.

## 🚀 Features

- **Granite Docling 258M**: OCR and document understanding model served via vLLM
- **Docling Serve**: GPU-accelerated document conversion API (PDF, DOCX, images → structured data)
- **LiteLLM API Gateway**: OpenAI-compatible API with authentication and cost tracking
- **Traefik Reverse Proxy**: Automatic HTTPS with Let's Encrypt
- **GPU Acceleration**: Optimized for NVIDIA L4 GPU (CUDA 13.0)

## 📋 Prerequisites

- Ubuntu 22.04 LTS (or similar)
- Docker with NVIDIA GPU support
- Domain names pointing to server IP:
  - `docling.ai-agents.ch` → `83.228.225.110` (LiteLLM API)
  - `serve.docling.ai-agents.ch` → `83.228.225.110` (Docling Serve)
- Ports 80 and 443 open for HTTP/HTTPS traffic

## 🔧 Installation

### 1. DNS Configuration

Ensure your domain points to the server:

```bash
# Check DNS resolution
nslookup docling.ai-agents.ch
nslookup serve.docling.ai-agents.ch
# Both should return: 83.228.225.110
```

### 2. Install Docker with GPU Support

```bash
# If not already installed
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu

# Install NVIDIA Container Toolkit (if not already installed)
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/libnvidia-container/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker

# Verify GPU access
docker run --rm --gpus all nvidia/cuda:12.4.0-base-ubuntu22.04 nvidia-smi
```

### 3. Deploy the Stack

```bash
# From your local machine, sync files to server
cd /home/thomas/Projects/aihub-core/aihub_ops/docling-deployment
make sync

# SSH to server
ssh test-gpu-instance

# Navigate to deployment directory
cd ~/docling-deployment

# Review and update .env file if needed
nano .env

# Start the stack
docker compose up -d

# Check logs
docker compose logs -f

# Wait for services to be healthy (vLLM takes ~2-3 minutes to load the model)
docker compose ps
```

## 🔐 Security Configuration

### Environment Variables

Edit `.env` to configure:

```bash
# Domain (already set to docling.ai-agents.ch)
DOMAIN=docling.ai-agents.ch
ACME_EMAIL=admin@ai-agents.ch

# API Key (secure random key pre-generated)
LITELLM_MASTER_KEY=sk-SZD87XrSBgcp9lCnTfMyQ-AMOet5ARCWUD7Ev0cOa5c

# Dashboard credentials (secure password pre-generated)
LITELLM_UI_USERNAME=admin
LITELLM_UI_PASSWORD=mtgRWcnx9nJz3xHbeQN0Ui5Aih0BoAFE
```

**Security Note**: The `.env` file contains secure randomly-generated credentials. Keep this file secret!

### Generate New API Key

```bash
openssl rand -base64 32
# Use output as new LITELLM_MASTER_KEY with 'sk-' prefix
```

## 📡 API Usage

### Base URL

```
https://docling.ai-agents.ch
```

### Authentication

Include your API key in the Authorization header:

```bash
Authorization: Bearer sk-SZD87XrSBgcp9lCnTfMyQ-AMOet5ARCWUD7Ev0cOa5c
```

### Example Request

```bash
curl -X POST https://docling.ai-agents.ch/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-SZD87XrSBgcp9lCnTfMyQ-AMOet5ARCWUD7Ev0cOa5c" \
  -d '{
    "model": "granite-docling",
    "messages": [
      {
        "role": "user",
        "content": "Extract text from this document..."
      }
    ],
    "max_tokens": 1000
  }'
```

### Python Example

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://docling.ai-agents.ch/v1",
    api_key="sk-SZD87XrSBgcp9lCnTfMyQ-AMOet5ARCWUD7Ev0cOa5c"
)

response = client.chat.completions.create(
    model="granite-docling",
    messages=[
        {"role": "user", "content": "Extract text from this document..."}
    ]
)

print(response.choices[0].message.content)
```

## 📄 Docling Serve API

Docling Serve provides GPU-accelerated document conversion (PDF, DOCX, PPTX, images → JSON/Markdown).

### Base URL

```
https://serve.docling.ai-agents.ch
```

### Authentication

Access is restricted by IP allowlist. Configure allowed IPs in `.env`:

```bash
DOCLING_SERVE_ALLOWED_IPS=192.168.1.0/24,10.0.0.1/32
```

### Health Check

```bash
curl https://serve.docling.ai-agents.ch/health
```

### Convert Document

```bash
# Convert PDF to JSON
curl -X POST https://serve.docling.ai-agents.ch/v1/convert/file \
  -F "files=@document.pdf" \
  -H "Accept: application/json"

# Convert to Markdown
curl -X POST https://serve.docling.ai-agents.ch/v1/convert/file \
  -F "files=@document.pdf" \
  -H "Accept: text/markdown"
```

### Python Example

```python
import httpx

with open("document.pdf", "rb") as f:
    response = httpx.post(
        "https://serve.docling.ai-agents.ch/v1/convert/file",
        files={"files": ("document.pdf", f, "application/pdf")},
        headers={"Accept": "application/json"},
    )

result = response.json()
print(result)
```

### Web UI

If enabled (`DOCLING_SERVE_ENABLE_UI=true`), access the UI at:

```
https://serve.docling.ai-agents.ch/ui
```

## 🎛️ Management

### Access LiteLLM Dashboard

Visit: https://docling.ai-agents.ch/ui

Login with credentials from `.env`:
- Username: `admin`
- Password: (value of `LITELLM_UI_PASSWORD`)

### Access Traefik Dashboard

Visit: https://docling.ai-agents.ch/dashboard/

### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f vllm-docling
docker compose logs -f litellm
docker compose logs -f docling-serve
docker compose logs -f traefik
```

### Check GPU Usage

```bash
# On the host
nvidia-smi

# From container
docker exec vllm-docling nvidia-smi
```

### Restart Services

```bash
# Restart all
docker compose restart

# Restart specific service
docker compose restart vllm-docling
docker compose restart litellm
```

### Stop Services

```bash
docker compose down
```

### Update Services

```bash
# Pull latest images
docker compose pull

# Restart with new images
docker compose up -d
```

## 📊 Monitoring

### Health Checks

```bash
# LiteLLM
curl https://docling.ai-agents.ch/health/liveliness

# vLLM
docker exec vllm-docling curl http://localhost:8000/health

# Docling Serve
curl https://serve.docling.ai-agents.ch/health
```

### Model Information

```bash
curl https://docling.ai-agents.ch/v1/models \
  -H "Authorization: Bearer sk-SZD87XrSBgcp9lCnTfMyQ-AMOet5ARCWUD7Ev0cOa5c"
```

## 🐛 Troubleshooting

### Services Not Starting

```bash
# Check logs
docker compose logs

# Check disk space
df -h

# Check GPU availability
nvidia-smi
```

### SSL Certificate Issues

```bash
# Check Traefik logs
docker compose logs traefik

# Verify DNS is pointing to correct IP
dig docling.ai-agents.ch

# Check acme.json permissions
ls -la traefik/acme.json
# Should be: -rw------- (600)
```

### Model Loading Issues

```bash
# Check vLLM logs
docker compose logs vllm-docling

# Model download can take time on first run
# Check HuggingFace cache
docker exec vllm-docling du -sh /root/.cache/huggingface
```

### Connection Refused

1. Check firewall rules:
```bash
sudo ufw status
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```

2. Verify Traefik is running:
```bash
docker compose ps traefik
```

3. Check container networking:
```bash
docker network ls
docker network inspect docling-deployment_default
```

## 📁 Directory Structure

```
docling-deployment/
├── docker-compose.yml          # Main deployment configuration
├── .env                        # Environment variables (secrets - NOT in git)
├── .env.example               # Environment template (safe to commit)
├── .gitignore                 # Git ignore patterns
├── Makefile                   # Deployment automation (make sync)
├── README.md                  # This file
├── traefik/
│   ├── traefik.yml            # Traefik static configuration
│   └── acme.json              # Let's Encrypt certificates (auto-generated)
└── litellm/
    └── config.yml             # LiteLLM model configuration
```

## 🔄 Backup & Restore

### Backup

```bash
# Backup configuration and certificates
tar -czf docling-backup-$(date +%Y%m%d).tar.gz \
  docker-compose.yml \
  .env \
  traefik/ \
  litellm/

# Backup Docker volumes
docker run --rm \
  -v docling-deployment_litellm-data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/litellm-data-$(date +%Y%m%d).tar.gz -C /data .
```

### Restore

```bash
# Restore configuration
tar -xzf docling-backup-YYYYMMDD.tar.gz

# Restore volumes
docker run --rm \
  -v docling-deployment_litellm-data:/data \
  -v $(pwd):/backup \
  alpine tar xzf /backup/litellm-data-YYYYMMDD.tar.gz -C /data
```

## 📝 Notes

- **GPU Memory**: vLLM is configured to use 90% of GPU memory (`--gpu-memory-utilization 0.90`)
- **Model Size**: Granite Docling 258M requires ~2GB VRAM
- **First Start**: Model download from HuggingFace can take 5-10 minutes on first run
- **SSL Certificates**: Let's Encrypt certificates auto-renew every 90 days
- **Logs**: Logs are limited to 10MB × 2 files per service

## 🆘 Support

For issues with:
- **Granite Docling**: https://github.com/DS4SD/docling
- **LiteLLM**: https://docs.litellm.ai/
- **vLLM**: https://docs.vllm.ai/
- **Traefik**: https://doc.traefik.io/traefik/

## 📄 License

Components:
- Granite Docling: Apache 2.0
- LiteLLM: MIT
- vLLM: Apache 2.0
- Traefik: MIT
