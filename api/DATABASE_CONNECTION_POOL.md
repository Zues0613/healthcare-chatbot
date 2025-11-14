# Persistent Database Connection Pool

## Overview

The database client now uses a **persistent connection pool** that stays alive throughout the application lifecycle. This eliminates unnecessary connection requests and improves performance.

## Key Features

### 1. **Persistent Connection Pool**
- Connection pool is created **once at application startup**
- Pool stays alive throughout the application lifecycle
- Connections are **reused** for all database queries
- No new connections created per request

### 2. **Connection Pool Settings**
```python
min_size=2                    # Keep at least 2 connections alive
max_size=20                   # Allow up to 20 concurrent connections
max_queries=50000            # Recycle connections after many queries
max_inactive_connection_lifetime=300  # Close idle connections after 5 minutes
```

### 3. **Automatic Health Monitoring**
- Background task checks connection health every 30 seconds
- Automatically detects dead connections
- Automatically reconnects if pool dies
- No manual intervention needed

### 4. **Automatic Reconnection**
- If a connection error occurs during a query, the system:
  1. Detects the error
  2. Automatically reconnects
  3. Retries the query
  4. Logs the incident

### 5. **Connection Setup**
Each connection in the pool is configured with:
- JSONB codec for efficient JSON handling
- Statement timeout (60 seconds)
- Optimized for NeonDB

## How It Works

### Startup
```python
@app.on_event("startup")
async def _startup():
    # Creates persistent connection pool
    await prisma_client.connect()
    # Pool stays alive for entire application lifecycle
```

### Query Execution
```python
# No connection overhead - just acquire from pool
async with pool.acquire() as conn:
    result = await conn.fetch("SELECT * FROM customers")
# Connection automatically returned to pool
```

### Shutdown
```python
@app.on_event("shutdown")
async def _shutdown():
    # Cleanly closes all connections in pool
    await prisma_client.disconnect()
```

## Benefits

1. **Performance**: No connection overhead per request
2. **Efficiency**: Connections are reused, not recreated
3. **Reliability**: Automatic reconnection on failures
4. **Scalability**: Pool handles concurrent requests efficiently
5. **Resource Management**: Idle connections are automatically cleaned up

## Connection Lifecycle

```
Application Start
    ↓
Create Connection Pool (2-20 connections)
    ↓
Pool Stays Alive (persistent)
    ↓
Request 1 → Acquire Connection → Use → Return to Pool
Request 2 → Acquire Connection → Use → Return to Pool
Request 3 → Acquire Connection → Use → Return to Pool
    ↓
Health Monitor Checks Every 30s
    ↓
Application Shutdown
    ↓
Close All Connections in Pool
```

## Monitoring

The system logs:
- Pool creation: `"Successfully created persistent PostgreSQL connection pool"`
- Health check failures: `"Connection health check failed"`
- Automatic reconnections: `"Attempting to reconnect to database..."`
- Pool closure: `"Closed PostgreSQL connection pool"`

## Error Handling

If a connection error occurs:
1. Error is caught (PostgresConnectionError, InterfaceError)
2. System logs warning
3. Automatically reconnects
4. Retries the query
5. Returns result or raises exception if retry fails

## Configuration

Connection pool settings can be adjusted in `api/database/db_client.py`:

```python
self.pool = await asyncpg.create_pool(
    database_url,
    min_size=2,      # Minimum connections
    max_size=20,      # Maximum connections
    command_timeout=60,  # Query timeout
    max_queries=50000,   # Connection recycling
    max_inactive_connection_lifetime=300,  # Idle timeout
)
```

## Best Practices

1. **Don't create new connections manually** - Use the pool
2. **Always use `async with pool.acquire()`** - Ensures proper cleanup
3. **Let the pool manage connections** - Don't close connections manually
4. **Monitor logs** - Watch for reconnection messages

## Troubleshooting

### Pool Not Connecting
- Check `NEON_DB_URL` environment variable
- Check network connectivity
- Check database server status

### Frequent Reconnections
- Check database server logs
- Check network stability
- Adjust `max_inactive_connection_lifetime` if needed

### Connection Timeouts
- Increase `command_timeout` if queries are slow
- Check database server performance
- Optimize slow queries

## Summary

The persistent connection pool ensures:
- ✅ **No unnecessary connection requests** - Pool stays alive
- ✅ **Automatic reconnection** - Handles failures gracefully
- ✅ **Health monitoring** - Detects issues proactively
- ✅ **Optimal performance** - Connections are reused efficiently
- ✅ **Resource management** - Idle connections are cleaned up

This implementation provides a robust, efficient database connection strategy that eliminates connection overhead while maintaining reliability.

