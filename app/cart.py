"""Core cart logic. Used by both the REST API and the MCP tools."""
import logging
from contextlib import closing

from .database import db

log = logging.getLogger("shop.cart")


def add_item(name: str, price: float, qty: int = 1) -> dict:
    with closing(db()) as c:
        cur = c.execute(
            "INSERT INTO cart(name, price, qty) VALUES (?,?,?)", (name, price, qty)
        )
        c.commit()
        log.info("Added item id=%s name=%s qty=%s", cur.lastrowid, name, qty)
        return {"id": cur.lastrowid, "name": name, "price": price, "qty": qty}


def list_items() -> dict:
    with closing(db()) as c:
        items = [dict(r) for r in c.execute("SELECT * FROM cart ORDER BY id")]
    total = round(sum(i["price"] * i["qty"] for i in items), 2)
    return {"items": items, "total": total}


def remove_item(item_id: int) -> bool:
    with closing(db()) as c:
        cur = c.execute("DELETE FROM cart WHERE id=?", (item_id,))
        c.commit()
        deleted = cur.rowcount > 0
        log.info("Removed item id=%s (deleted=%s)", item_id, deleted)
        return deleted
