"""MCP server: exposes the cart as tools for AI agents."""
import functools
import logging

from mcp.server.fastmcp import FastMCP

from . import cart
from .metrics import MCP_CALLS

log = logging.getLogger("shop.mcp")

mcp = FastMCP(
    "shop-cart",
    stateless_http=True,
    json_response=True,
    streamable_http_path="/",
)


def tracked(fn):
    """Log + count every MCP tool call (keeps the original signature via wraps)."""

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            log.info("MCP tool=%s args=%s kwargs=%s", fn.__name__, args, kwargs)
            result = fn(*args, **kwargs)
            MCP_CALLS.labels(fn.__name__, "true").inc()
            return result
        except Exception:
            MCP_CALLS.labels(fn.__name__, "false").inc()
            log.exception("MCP tool failed: %s", fn.__name__)
            raise

    return wrapper


@mcp.tool()
@tracked
def add_to_cart(name: str, price: float, qty: int = 1) -> dict:
    """Add a product to the shopping cart."""
    return cart.add_item(name, price, qty)


@mcp.tool()
@tracked
def view_cart() -> dict:
    """Show all cart items and the total."""
    return cart.list_items()


@mcp.tool()
@tracked
def remove_from_cart(item_id: int) -> str:
    """Remove an item from the cart by its id."""
    return "removed" if cart.remove_item(item_id) else "not found"
