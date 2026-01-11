# Authentication Guide

## Overview

InsightGraph uses **API Key authentication** to secure mutation endpoints (POST, DELETE operations).

### Security Model

- **Public Endpoints** (Read-only, Rate-limited):
  - `GET /health` - Health check
  - `GET /stats` - System statistics
  - `GET /rate-limit-status` - Rate limit info
  - `GET /graphs` - List graphs
  - `GET /graphs/{id}` - Get specific graph
  - `GET /graphs/search` - Search graphs

- **Secured Endpoints** (Require API Key):
  - `POST /graphs` - Create and save graph
  - `DELETE /graphs/{id}` - Delete graph

- **Rate-Limited Public** (No API key required):
  - `POST /extract` - Extract knowledge graph (in-memory)
  - `POST /jobs` - Create async job
  - `GET /jobs/{id}` - Get job status

## Setup

### 1. Generate an API Key

```bash
# Generate a secure API key (32 bytes)
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 2. Configure Environment

Add to your `.env` file:

```bash
API_KEY=your_generated_key_here
```

### 3. Restart the Server

```bash
cd backend
uvicorn main:app --reload
```

You should see:
```
[OK] API Key: Set (length: 43) - Authentication enabled
```

## Usage

### Without Authentication (Development Mode)

If `API_KEY` is not set, all endpoints are public:

```bash
# This works without API key
curl -X POST http://localhost:8000/graphs \
  -H "Content-Type: application/json" \
  -d '{"text": "Python is awesome"}'
```

### With Authentication (Production Mode)

When `API_KEY` is set, secured endpoints require the `X-API-Key` header:

```bash
# This requires API key
curl -X POST http://localhost:8000/graphs \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_key_here" \
  -d '{"text": "Python is awesome"}'
```

Without the key, you'll get:
```json
{
  "detail": "API key required. Provide X-API-Key header."
}
```

With an invalid key:
```json
{
  "detail": "Invalid API key"
}
```

## Check Authentication Status

```bash
curl http://localhost:8000/stats
```

Response includes:
```json
{
  "authentication": {
    "enabled": true
  }
}
```

## Best Practices

### Development
- Leave `API_KEY` empty in `.env` for easier testing
- All endpoints work without authentication
- Still protected by rate limiting

### Production
- **ALWAYS** set `API_KEY` to a secure random value
- Use environment variables, not hardcoded values
- Rotate keys periodically
- Use HTTPS to protect key in transit
- Never commit `.env` to version control

### CI/CD
- Set `API_KEY` as a secret in your CI/CD system
- Use different keys for staging/production
- Automate key rotation

## Examples

### Create Graph (Authenticated)

```bash
curl -X POST http://localhost:8000/graphs \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_key_here" \
  -d '{
    "text": "FastAPI is a Python framework",
    "title": "FastAPI Graph"
  }'
```

### Delete Graph (Authenticated)

```bash
curl -X DELETE http://localhost:8000/graphs/{graph-id} \
  -H "X-API-Key: your_api_key_here"
```

### List Graphs (Public)

```bash
# No API key needed
curl http://localhost:8000/graphs
```

### Extract Graph (Public, Rate-Limited)

```bash
# No API key needed, but rate-limited
curl -X POST http://localhost:8000/extract \
  -H "Content-Type: application/json" \
  -d '{"text": "Python is used for data science"}'
```

## Implementation Details

### Architecture

Authentication is implemented using:
- `middleware/api_key_auth.py` - Authentication middleware
- `config.py` - API_KEY configuration
- FastAPI `Security` dependency injection

### Code Example

```python
from middleware.api_key_auth import require_api_key
from fastapi import Depends, APIRouter

router = APIRouter()

@router.post("/secure", dependencies=[Depends(require_api_key)])
async def secure_endpoint():
    return {"message": "This endpoint is protected"}
```

### Flexible Security

The middleware gracefully handles missing keys:
- If `API_KEY` is not configured → All endpoints are public
- If `API_KEY` is configured → Secured endpoints require key
- Read-only endpoints always public (good for API consumers)

## Troubleshooting

### Issue: 401 Unauthorized

**Cause**: Missing or invalid API key

**Solution**:
1. Check `.env` file has `API_KEY` set
2. Ensure you're sending `X-API-Key` header
3. Verify the key matches exactly (no extra spaces)

### Issue: Endpoints still public after setting API_KEY

**Cause**: Server not restarted

**Solution**: Restart the FastAPI server to load new config

### Issue: Can't create graphs in development

**Cause**: Accidentally set API_KEY in development

**Solution**: Remove or comment out `API_KEY` in `.env` for local dev

## Future Enhancements

Potential improvements (not yet implemented):
- [ ] Multiple API keys (per-user, per-service)
- [ ] JWT tokens for user authentication
- [ ] OAuth2 integration
- [ ] Role-based access control (RBAC)
- [ ] API key expiration
- [ ] Rate limiting per API key
