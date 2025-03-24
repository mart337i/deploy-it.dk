from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
import os
import platform
import sys
import psutil
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from clicx.utils.jinja import render, _env
from clicx.config import templates_dir, configuration

router = APIRouter(prefix="/debug", tags=["debug"])

dependency = []

start_time = time.time()
logger = logging.getLogger("debug")

@router.get("/", response_class=HTMLResponse)
async def debug_dashboard(request: Request):
    """
    Renders the debug dashboard
    """
    # Calculate uptime
    uptime_seconds = time.time() - start_time
    uptime = str(timedelta(seconds=int(uptime_seconds)))
    
    # Get memory usage
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    memory_usage = f"{memory_info.rss / (1024 * 1024):.2f} MB"
    memory_percent = f"{process.memory_percent():.1f}%"
    
    # Get status information
    app_status = {
        "status": "ok",
        "message": "Running",
        "uptime": uptime
    }
    
    memory_status = {
        "status": "ok" if process.memory_percent() < 75 else "warning",
        "usage": memory_usage,
        "percentage": memory_percent
    }
    
    # Try to get some recent logs
    logs = get_recent_logs(20)
    
    # Get available templates
    templates = get_templates_list()
    
    # Get routes
    routes = get_routes(request)
    
    # Get environment variables (filtered for security)
    env_vars = get_safe_env_vars()
    
    # Prepare context for the template
    context = {
        "request": request,
        "app_name": "API Platform",
        "title": "Debug Dashboard",
        "environment": os.getenv("ENVIRONMENT", "Development"),
        "app_status": app_status,
        "memory_status": memory_status,
        "templates": templates,
        "routes": routes,
        "env_vars": env_vars,
        "logs": logs
    }
    
    # Render the debug template
    html_content = render("debug.html.jinja", context=context)
    return HTMLResponse(content=html_content)

@router.get("/templates")
async def list_templates():
    templates = _env.list_templates()
    return {
        "ok": templates,
    }


@router.get("/system-info")
async def system_info():
    """
    Returns system information
    """
    cpu_percent = psutil.cpu_percent(interval=0.5)
    mem = psutil.virtual_memory()
    
    system_info = {
        "platform": platform.platform(),
        "python_version": sys.version,
        "cpu_count": psutil.cpu_count(),
        "cpu_percent": f"{cpu_percent}%",
        "memory_total": f"{mem.total / (1024 * 1024 * 1024):.2f} GB",
        "memory_available": f"{mem.available / (1024 * 1024 * 1024):.2f} GB",
        "memory_percent_used": f"{mem.percent}%",
    }
    
    return {
        "ok": system_info,
    }

def get_routes(request: Request) -> List[Dict[str, str]]:
    """
    Get a list of all routes in the application
    """
    routes_list = []
    
    try:
        # Get the main FastAPI app from the request
        app = request.app
        
        # Loop through all routes
        for route in app.routes:
            # Skip the WebSocket routes
            if hasattr(route, "methods"):
                for method in route.methods:
                    routes_list.append({
                        "path": route.path,
                        "method": method,
                        "name": getattr(route, "name", ""),
                    })
    except Exception as e:
        logger.error(f"Error listing routes: {str(e)}")
    
    # Sort routes by path
    routes_list.sort(key=lambda x: x["path"])
    
    return routes_list

def get_safe_env_vars() -> Dict[str, str]:
    """
    Get a filtered list of environment variables, excluding sensitive ones
    """
    # Define patterns or prefixes for sensitive variables to exclude
    sensitive_patterns = [
        "key", "secret", "token", "password", "auth", "credential", "api_key",
        "private", "cert", "ssh", "ssl", "jwt", "oauth", "pass", "pwd"
    ]
    
    safe_env = {}
    
    for key, value in os.environ.items():
        # Skip sensitive variables
        if any(pattern in key.lower() for pattern in sensitive_patterns):
            safe_env[key] = "******** [REDACTED]"
        else:
            safe_env[key] = value
    
    return dict(sorted(safe_env.items()))

def get_recent_logs(count: int = 20, level: str = "all") -> List[str]:
    """
    Get recent log entries
    In a real application, this would read from your log files or a logging database
    """
    # This is just a sample implementation
    # In a real app, you'd read from actual log files or a logging service
    
    log_level_filter = level.upper() if level != "all" else None
    
    sample_logs = [
        "2025-03-23 08:01:23 INFO     Server started successfully",
        "2025-03-23 08:01:24 INFO     Database connection established",
        "2025-03-23 08:02:15 DEBUG    Cache initialized with TTL=300s",
        "2025-03-23 08:05:32 INFO     Request received: GET /api/items",
        "2025-03-23 08:05:32 DEBUG    Query executed in 12ms",
        "2025-03-23 08:06:45 WARNING  Slow query detected (324ms): SELECT * FROM large_table",
        "2025-03-23 08:10:22 ERROR    Failed to connect to external service: timeout",
        "2025-03-23 08:12:54 INFO     User authentication successful: user_id=1234",
        "2025-03-23 08:15:33 DEBUG    Cache hit for key: 'items_list'",
        "2025-03-23 08:18:44 INFO     Request received: POST /api/items",
        "2025-03-23 08:18:45 INFO     New item created: id=42",
        "2025-03-23 08:20:01 WARNING  Rate limit approaching for IP: 192.168.1.42",
        "2025-03-23 08:25:18 ERROR    Database query failed: relation 'missing_table' does not exist",
        "2025-03-23 08:30:05 INFO     Scheduled task started: cleanup_old_data",
        "2025-03-23 08:30:08 INFO     Deleted 156 expired records",
        "2025-03-23 08:35:12 DEBUG    Configuration reloaded from file",
        "2025-03-23 08:40:33 WARNING  High memory usage detected: 78%",
        "2025-03-23 08:45:22 INFO     Request received: GET /api/items/123",
        "2025-03-23 08:46:18 ERROR    Item not found: id=999",
        "2025-03-23 08:50:01 INFO     Request received: PUT /api/items/42",
    ]
    
    # If a specific log level is requested, filter the logs
    if log_level_filter:
        filtered_logs = [log for log in sample_logs if log_level_filter in log]
        return filtered_logs[-count:] if filtered_logs else []
    
    # Otherwise, return all logs up to the count
    return sample_logs[-count:]

def get_templates_list() -> List[str]:
    """
    Get a list of available templates from the templates directory
    """
    return _env.list_templates()