"""FastAPI app: REST API + MCP mount + metrics + static page."""
import logging
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from pydantic import BaseModel, Field

from . import cart
from .database import init_db
from .logging_conf import setup_logging
from .mcp_server import mcp
from .metrics import LATENCY, REQUESTS

setup_logging()
log = logging.getLogger("shop")

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


class ItemIn(BaseModel):
    name: str = Field(min_length=1)
    price: float = Field(gt=0)
    qty: int = Field(default=1, ge=1)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    log.info("App started")
    async with mcp.session_manager.run():  # required for MCP inside FastAPI
        yield
    log.info("App stopped")


app = FastAPI(title="Shopping Cart + MCP", lifespan=lifespan)


@app.middleware("http")
async def monitor(request: Request, call_next):
    start = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        log.exception("Unhandled error on %s %s", request.method, request.url.path)
        REQUESTS.labels(request.method, request.url.path, 500).inc()
        raise
    took = time.perf_counter() - start
    route = request.scope.get("route")
    path = getattr(route, "path", request.url.path)  # template, e.g. /api/cart/{item_id}
    REQUESTS.labels(request.method, path, response.status_code).inc()
    LATENCY.labels(path).observe(took)
    log.info("%s %s -> %s (%.1f ms)", request.method, request.url.path,
             response.status_code, took * 1000)
    return response


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/cart")
def api_add(item: ItemIn):
    return cart.add_item(item.name, item.price, item.qty)


@app.get("/api/cart")
def api_list():
    return cart.list_items()


@app.delete("/api/cart/{item_id}")
def api_remove(item_id: int):
    if not cart.remove_item(item_id):
        raise HTTPException(404, "Item not found")
    return {"deleted": item_id}


@app.get("/metrics", include_in_schema=False)
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.api_route("/mcp", methods=["GET", "POST", "DELETE"], include_in_schema=False)
def mcp_no_slash():
    return RedirectResponse("/mcp/", status_code=307)  # 307 keeps the HTTP method


app.mount("/mcp", mcp.streamable_http_app())
# Keep this LAST: it serves the single page at "/"
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
