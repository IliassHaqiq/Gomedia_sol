# Ollama Integration Guide

This guide helps you configure GoMedia to use Ollama as the local LLM backend.

## Prerequisites

- [Ollama](https://ollama.com/download) installed
- At least 8 GB RAM recommended for larger models
- A pulled model matching `OLLAMA_MODEL` in `.env`

## Quick Setup

### 1. Copy environment file

```bash
cp .env.ollama.example .env
```

### 2. Install and start Ollama

```bash
# Windows
winget install ollama
ollama serve

# macOS / Linux
curl -fsSL https://ollama.com/install.sh | sh
ollama serve
```

### 3. Pull a model

```bash
ollama pull llama3.2:latest
```

### 4. Configure `.env`

```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:latest
OLLAMA_TIMEOUT=180
```

### 5. Verify integration

```bash
python verify_ollama.py
```

### 6. Start the API

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | `llama3.2:latest` | Model name (`ollama list`) |
| `OLLAMA_TIMEOUT` | `180` | Request timeout (seconds) |
| `OLLAMA_MAX_RETRIES` | `3` | Retry attempts on failure |
| `OLLAMA_REQUEST_INTERVAL` | `0` | Delay between requests (seconds) |

## Recommended Models

| Model | RAM | Use case |
|-------|-----|----------|
| `llama3.2:latest` | ~4 GB | Good balance of speed and quality |
| `llama3.2:3b` | ~2 GB | Faster, lighter extractions |
| `mistral:latest` | ~4 GB | Strong technical writing |
| `qwen2.5:7b` | ~5 GB | Good multilingual FR/EN |

Pull a model before use:

```bash
ollama pull mistral:latest
```

Then set `OLLAMA_MODEL=mistral:latest` in `.env`.

## Health Check

```bash
curl http://localhost:8000/health/ollama
```

## Troubleshooting

### Cannot connect to Ollama

- Ensure Ollama is running: `ollama serve`
- Test: `curl http://localhost:11434/api/tags`

### Model not found (404)

```bash
ollama pull llama3.2:latest
```

### Timeouts on long descriptions

- Use description length `short` in the UI
- Increase `OLLAMA_TIMEOUT=300`
- Use a smaller model (`llama3.2:3b`)

### Slow generation

- Use a smaller model
- Close other GPU/CPU heavy applications
- Reduce `OLLAMA_REQUEST_INTERVAL` if set

## API Used

GoMedia calls Ollama's native chat API:

```
POST {OLLAMA_BASE_URL}/api/chat
```

No API key is required for local Ollama.
