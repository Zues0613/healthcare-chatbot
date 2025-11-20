# Deployment Guide: Vercel vs Render

This healthcare chatbot is **compatible with both Vercel and Render**, but with important considerations for each platform.

## Platform Comparison

| Feature | Render (Recommended) | Vercel (Serverless) |
|---------|---------------------|---------------------|
| **Deployment Type** | Traditional Web Service | Serverless Functions |
| **Best For** | Long-running, persistent connections | API endpoints, edge functions |
| **Cold Starts** | Minimal (always warm) | Common (each function invocation) |
| **Execution Time** | Unlimited | 10s (Free), 60s (Pro), 300s (Enterprise) |
| **Background Tasks** | ✅ Full support | ⚠️ Limited (may not complete) |
| **Persistent Connections** | ✅ Perfect | ⚠️ Needs connection pooling adapter |
| **Startup Events** | ✅ Full support | ⚠️ Limited (may not run) |

---

## ✅ Render Deployment (Recommended)

**Status**: ✅ Fully Compatible

### Why Render is Recommended:
- ✅ Persistent database connections (Neo4j, PostgreSQL, Redis)
- ✅ Background tasks complete successfully
- ✅ Startup events initialize connections properly
- ✅ No execution time limits
- ✅ Better for long-running AI generation (90s timeout)

### Configuration (Already Set Up):

**File**: `render.yaml`
```yaml
services:
  - type: web
    name: healthcare-chatbot-api
    env: python
    buildCommand: pip install -r api/requirements.txt
    predeployCommand: python api/rag/build_index.py || echo "Index build completed"
    startCommand: uvicorn api.main:app --host 0.0.0.0 --port $PORT
    plan: starter
    envVars:
      - key: ENVIRONMENT
        value: production
```

### Required Environment Variables:
```bash
# Database
DATABASE_URL=postgresql://...
NEO4J_URI=bolt://...
NEO4J_USER=neo4j
NEO4J_PASSWORD=...

# Cache
REDIS_URI=redis://...

# AI Services
OPENAI_API_KEY=sk-...
OPENROUTER_API_KEY=...

# Performance (Optional)
AI_GENERATION_TIMEOUT=90.0  # Timeout for AI generation (seconds)

# Other
ENVIRONMENT=production
CORS_ORIGINS=https://your-frontend.com
```

### Deployment Steps:
1. Push code to GitHub
2. Connect repository to Render
3. Render auto-detects `render.yaml`
4. Set environment variables in Render dashboard
5. Deploy!

---

## ⚠️ Vercel Deployment (Serverless)

**Status**: ⚠️ Compatible with Limitations

### Limitations:
1. **Execution Time Limits**:
   - Free tier: 10 seconds max
   - Pro tier: 60 seconds max
   - Enterprise: 300 seconds max
   - **Our AI generation timeout is 90s** - This exceeds Pro tier limits! ⚠️

2. **Background Tasks**:
   - FastAPI `BackgroundTasks` may not complete
   - Message saving might fail silently
   - **Workaround**: Use synchronous saving or external queue (e.g., Vercel Queue)

3. **Startup Events**:
   - `@app.on_event("startup")` may not run reliably
   - Connections might need lazy initialization
   - **Workaround**: Initialize connections on first request

4. **Persistent Connections**:
   - Serverless functions are stateless
   - Connection pooling needs adapter pattern
   - **Workaround**: Use connection pool per function invocation

### Vercel Configuration:

**File**: `vercel.json` (Create if deploying to Vercel)
```json
{
  "version": 2,
  "builds": [
    {
      "src": "api/main.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "api/main.py"
    }
  ],
  "functions": {
    "api/main.py": {
      "maxDuration": 300
    }
  },
  "env": {
    "ENVIRONMENT": "production"
  }
}
```

### Required Changes for Vercel:

1. **Set AI Generation Timeout** (to fit within Pro tier):
   ```bash
   # In Vercel dashboard, set environment variable:
   AI_GENERATION_TIMEOUT=60.0  # Reduced from 90s to 60s for Vercel Pro
   ```
   ⚠️ **Note**: This is already configurable via `AI_GENERATION_TIMEOUT` env var (default: 90.0s)

2. **Startup Events**: 
   - Already handled - connections initialize lazily via `ensure_neo4j()`, etc.
   - No changes needed!

3. **Background Tasks**: 
   - FastAPI `BackgroundTasks` may not complete on serverless
   - Option: Use Vercel Queue or save messages synchronously (code already handles failures gracefully)

### Vercel Environment Variables:
Same as Render (set in Vercel dashboard).

---

## 🎯 Recommended Approach

### For Production: **Use Render** ✅
- Better for AI workloads with long generation times
- Reliable background task completion
- Persistent connections work out of the box
- No execution time worries

### For Development/Testing: **Vercel** ⚠️
- Good for API endpoints
- Faster deployments
- But may hit timeout limits on complex queries

---

## 📊 Performance Expectations

### Render:
- **Cold Start**: ~2-3 seconds (first request)
- **Warm Requests**: 2-5 seconds (English), 5-10 seconds (with translation)
- **Background Tasks**: Complete reliably

### Vercel:
- **Cold Start**: ~3-5 seconds (serverless function initialization)
- **Warm Requests**: 3-6 seconds (English), 6-12 seconds (with translation)
- **Background Tasks**: May not complete (use Vercel Queue or synchronous saving)

---

## 🔧 Platform Detection

The code already handles platform differences:

```python
# Connections initialize lazily if startup fails
if ensure_neo4j():
    # Use Neo4j
else:
    # Fallback to in-memory graph
```

This makes it compatible with both platforms!

---

## 🚀 Deployment Checklist

### Before Deploying:

- [ ] Set all environment variables in platform dashboard
- [ ] Verify database connections are accessible from platform
- [ ] Test Neo4j connection (if using)
- [ ] Test Redis connection (if using)
- [ ] Verify CORS_ORIGINS includes frontend URL
- [ ] Run `python api/rag/build_index.py` (or let predeployCommand handle it)

### After Deploying:

- [ ] Check health endpoint: `GET /health`
- [ ] Test chat endpoint: `POST /chat`
- [ ] Verify conversation history saves correctly
- [ ] Monitor logs for connection errors
- [ ] Test with different languages

---

## 📝 Notes

1. **Execution Time**: 
   - **Vercel Pro (60s limit)**: Set `AI_GENERATION_TIMEOUT=60.0` in environment variables
   - **Vercel Enterprise (300s limit)**: Can use default `90.0` or increase to `120.0` for complex queries
   - **Render (unlimited)**: Default `90.0` is fine, can increase if needed

2. **Timeout Configuration**:
   - Configurable via `AI_GENERATION_TIMEOUT` environment variable
   - Default: `90.0` seconds
   - Vercel Pro: Set to `60.0` seconds
   - Vercel Enterprise: Can use `90.0` or higher

2. **Background Tasks**: On Vercel, consider using:
   - Vercel Queue (recommended)
   - Synchronous saving (simpler, but blocks response)
   - External task queue (e.g., Redis Queue, Celery)

3. **Connection Pooling**: Both platforms benefit from connection pooling, but Render is more forgiving with persistent connections.

4. **Monitoring**: Set up error tracking (e.g., Sentry) to monitor connection failures and timeouts.

---

## 🆘 Troubleshooting

### Issue: Connections timeout on Vercel
**Solution**: Increase timeout or use connection pool adapter for serverless.

### Issue: Background tasks don't complete on Vercel
**Solution**: Use Vercel Queue or save messages synchronously.

### Issue: Startup events don't run on Vercel
**Solution**: Initialize connections lazily on first request (already implemented).

### Issue: Execution time exceeded on Vercel
**Solution**: Upgrade to Vercel Enterprise (300s) or optimize pipeline further.

---

## ✅ Summary

- **Render**: ✅ Fully compatible, recommended for production
- **Vercel**: ⚠️ Compatible with limitations (execution time, background tasks)
- **Code**: Already handles platform differences gracefully
- **Migration**: Easy to switch between platforms (just change environment variables)

