"""Prometheus metrics."""
from prometheus_client import Counter, Histogram

REQUESTS = Counter("http_requests_total", "Total HTTP requests", ["method", "path", "status"])
LATENCY = Histogram("http_request_seconds", "HTTP request latency (seconds)", ["path"])
MCP_CALLS = Counter("mcp_tool_calls_total", "MCP tool calls", ["tool", "ok"])
