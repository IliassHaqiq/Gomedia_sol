# NVIDIA NIM Integration Guide

This guide will help you configure your GoMedia application to use NVIDIA NIM instead of Gemini.

## Prerequisites

- NVIDIA GPU (optional but recommended for local deployment)
- NVIDIA NIM API key from https://build.nvidia.com
- Docker (if running locally)

## Quick Start

### 1. Rename `.env.nim.example` to `.env`

```bash
cp .env.nim.example .env
```

### 2. Get your NVIDIA NIM API Key

1. Visit [build.nvidia.com](https://build.nvidia.com)
2. Create an account or sign in
3. Select "Llama 3 70B Instruct" model (or another model)
4. Click "Get API Key"
5. Copy your key (starts with `nvapi-...`)

### 3. Configure the environment

Edit the `.env` file:

```bash
# .env file
NIM_API_KEY=nvapi-your-key-here
NIM_MODEL=meta/llama-3-70b-instruct
NIM_API_URL=https://integrate.api.nvidia.com/v1

DATABASE_URL=postgresql://your_db_credentials
```

### 4. Verify configuration

```bash
python -m app.verify_nim
```

### 5. Run your application

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API Rate Limits

NVIDIA NIM allows **40 requests per minute**.

The code includes automatic rate limiting that:
- Waits 1.5 seconds between requests
- Respects the API rate limit automatically
- Shows clear error messages if exceeded

### Batch Processing

For best performance with multiple files, use the extract-all endpoint:

```bash
curl -X POST "http://localhost:8000/documents/extract-all?description_length=medium"
```

This will process files sequentially with automatic rate limiting.

## Local NIM Deployment (Optional)

If you have a powerful NVIDIA GPU, you can run NIM locally:

### System Requirements

- **GPU**: 2x A100 80GB, 2x H100 80GB, 4x A100-PCIE-40GB, 4x H100-PCIE-64GB, or 8x A30
- **RAM**: 180GB
- **Storage**: 300GB
- **Network**: Single NIC, 10G recommended

### Docker Deployment

1. **Get NGC API Key**
   ```bash
   # Go to https://ngc.nvidia.com and generate an API key
   export NGC_API_KEY="your-ngc-key"
   ```

2. **Run NIM Container**
   ```bash
   export LOCAL_NIM_CACHE=~/.cache/nim
   mkdir -p $LOCAL_NIM_CACHE

   docker run -d --rm \
     --gpus all \
     --name nim-llama3 \
     -e NGC_API_KEY=$NGC_API_KEY \
     -v $LOCAL_NIM_CACHE:/opt/nim/.cache \
     -p 8000:8000 \
     nvcr.io/nim/meta/llama-3-70b-instruct:latest
   ```

3. **Wait for model download**
   - First run downloads ~140GB of model data
   - Takes 15-30 minutes depending on connection speed
   - Check logs: `docker logs -f nim-llama3`

4. **Update `.env`**
   ```bash
   NIM_API_URL=http://localhost:8000/v1
   NIM_API_KEY=ngc-key-if-needed  # May not need for local
   NIM_MODEL=meta/llama-3-70b-instruct
   ```

### Verifying Local NIM

```bash
# Check if NIM is running
curl http://localhost:8000/v1/health

# Expected response: {"status":"ready"}

# Test a simple query
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "meta/llama-3-70b-instruct",
    "messages": [{"role": "user", "content": "Hello"}],
    "max_tokens": 10
  }'
```

## Model Options

NVIDIA offers several models. Here are the most suitable for your use case:

### Recommended Models

| Model | Speed | Quality | Cost | Use Case |
|-------|-------|---------|------|----------|
| meta/llama-3-70b-instruct | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Medium | **Default** - Best balance |
| meta/llama-3-8b-instruct | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Low | Faster, cheaper, good quality |
| microsoft/phi-3.5-mini-instruct | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | Very Low | Very fast, budget option |
| google/gemma-2-27b-it | ⭐⭐⭐ | ⭐⭐⭐⭐ | Low | Good quality, moderate speed |

### Longer Context Models (for large PDFs/Excel files)

| Model | Max Tokens | Use Case |
|-------|------------|----------|
| meta/llama-3-70b-instruct | 4096 | Large documents |
| meta/llama-3.1-405b-instruct | 8092 | Very large documents |

### Cost Optimization

For production with many users, consider:

1. **Use smaller model for batch processing**:
   ```bash
   # User-facing: Llama 3 70B
   NIM_MODEL=meta/llama-3-70b-instruct

   # Batch processing: Llama 3 8B
   NIM_MODEL=meta/llama-3-8b-instruct
   ```

2. **Implement model routing**:
   ```python
   # In your code
   small_text = len(text) < 1000
   if small_text:
       model = "meta/llama-3-8b-instruct"
   else:
       model = "meta/llama-3-70b-instruct"
   ```

## Troubleshooting

### Problem: `Invalid NIM_API_KEY`

**Solution:**
- Verify your API key is correct
- Check if your key has expired (check at build.nvidia.com)
- Ensure no extra spaces in `.env` file

```bash
# Test your key directly
curl https://integrate.api.nvidia.com/v1/models \
  -H "Authorization: Bearer nvapi-your-key-here"
```

### Problem: `Rate limit exceeded`

**Solution:**
- The code handles this automatically with `rate_limit()` function
- For large batches, wait between calls:
  ```python
  import time
  for doc in documents:
      process(doc)
      time.sleep(1.5)  # Wait for rate limit
  ```

### Problem: `Cannot connect to NIM`

**Solution:**
- Check your internet connection
- Verify NIM_API_URL is correct:
  - Cloud: `https://integrate.api.nvidia.com/v1`
  - Local: `http://localhost:8000/v1`
- If local, ensure Docker container is running: `docker ps`

### Problem: `Empty response from NIM`

**Solution:**
- Reduce `max_tokens` value (try 2000)
- Simplify your prompt
- Check if the model is still loading (local deployment)

### Problem: Large files fail

**Solution:**
- Increase `truncate_text` limit in extractor.py
- Use a model with larger context window
- Split the document into chunks

```python
# In app/services/extractor.py
MAX_TEXT_LENGTH = 8000  # Increase from 6000
```

### Problem: JSON parsing errors

**Solution:**
- Increase temperature (try 0.3) for more variety
- Check if NIM_MODEL uses correct format
- Add retry logic:
  ```python
  try:
      raw = _post_to_nim(prompt)
      data = _extract_json(raw)
  except ValueError:
      # Retry once
      raw = _post_to_nim(prompt)
      data = _extract_json(raw)
  ```

## Monitoring and Logging

Enable detailed logging in your `.env`:

```bash
LOG_LEVEL=DEBUG
```

Check API usage on your NVIDIA account:
https://build.nvidia.com/metrics

## Backup Gemini Configuration (Optional)

Keep the old Gemini config as fallback:

```python
# In your .env
# Gemini fallback
GEMINI_API_KEY=your-gemini-key
GEMINI_MODEL=models/gemini-1.5-pro

# In your code (modify llm.py)
def _post_to_llm(prompt):
    try:
        return _post_to_nim(prompt)
    except Exception as e:
        print(f"NIM failed, using Gemini: {e}")
        return _post_to_gemini(prompt)
```

## Performance Benchmarks (Cloud NIM)

Typical response times on cloud NIM:

| Operation | Llama 3 8B | Llama 3 70B |
|-----------|------------|-------------|
| PDF extraction (2 pages) | 2-3s | 3-5s |
| Excel extraction (50 rows) | 1-2s | 2-3s |
| Large PDF (10 pages) | 8-10s | 12-18s |
| Batch of 10 docs | 25-30s | 45-60s |

*Times include automatic rate limiting wait times*

## Support and Documentation

- **NVIDIA NIM Documentation**: https://docs.nvidia.com/nim/large-language-models/latest/overview.html
- **API Reference**: https://docs.nvidia.com/nim/large-language-models/latest/flow-api-endpoints.html
- **Model Catalog**: https://build.nvidia.com/explore/reasoning
- **Workload Management**: https://docs.nvidia.com/cloud-workstations/nims-deployment/lws/lws-user-guide.html

## Next Steps

1. ✅ Get your NIM API key
2. ✅ Update `.env` file
3. ✅ Test API connectivity
4. ✅ Run your application
5. ✅ Monitor usage via NVIDIA dashboard
6. 🔄 Consider local deployment for sensitive data
7. 🔄 Implement monitoring and alerting
8. 📊 Track costs and optimize model selection

---

**Need help?** Check your application logs in `logs/app.log` for detailed debug information.
