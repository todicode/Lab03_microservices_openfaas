import hashlib
import json
import logging
import os
import uuid

import requests
from psycopg.types.json import Jsonb

from .common import (APIError, api, body, connect, header, health, identifier, integer,
                     method_not_allowed, not_found, result, route, text)

LOGGER = logging.getLogger(__name__)


def upstream(service, path, payload=None):
    gateway = os.environ.get("GATEWAY_URL", "http://gateway.openfaas:8080").rstrip("/")
    try:
        response = requests.request("POST" if payload is not None else "GET",
                                    f"{gateway}/function/{service}{path}", json=payload,
                                    timeout=(2, 5))
    except requests.Timeout:
        raise APIError(504, "upstream_timeout", f"{service} phản hồi quá chậm. Chưa tạo đơn hàng.") from None
    except requests.RequestException:
        raise APIError(502, "upstream_unavailable", f"Chưa kết nối được {service}. Chưa tạo đơn hàng.") from None
    if response.status_code == 404 and service == "product-service":
        raise APIError(400, "product_unavailable", "Một sản phẩm không còn tồn tại.")
    if not response.ok:
        raise APIError(502, "upstream_error", f"{service} chưa xử lý được yêu cầu. Chưa tạo đơn hàng.")
    try:
        return response.json()
    except ValueError:
        raise APIError(502, "upstream_error", "Service phụ thuộc trả dữ liệu không hợp lệ.") from None


def order_input(event):
    data = body(event)
    customer = {"name": text(data, "customer_name", 120), "phone": text(data, "phone", 30),
                "address": text(data, "address", 500), "note": text(data, "note", 500, False)}
    raw_items = data.get("items")
    if not isinstance(raw_items, list) or not 1 <= len(raw_items) <= 50:
        raise APIError(400, "invalid_items", "Đơn hàng cần từ 1 đến 50 sản phẩm.")
    quantities = {}
    for item in raw_items:
        if not isinstance(item, dict):
            raise APIError(400, "invalid_items", "Mỗi dòng sản phẩm phải là object.")
        pid = identifier(item.get("product_id"))
        quantity = integer(item.get("quantity"), "quantity", 1, 99)
        quantities[pid] = integer(quantities.get(pid, 0) + quantity, "quantity", 1, 99)
    items = [{"product_id": pid, "quantity": quantities[pid]} for pid in sorted(quantities)]
    canonical = {"customer": customer, "items": items}
    fingerprint = hashlib.sha256(json.dumps(canonical, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    key = header(event, "Idempotency-Key") or str(uuid.uuid4())
    if len(key) > 100 or not key.isascii() or not all(c.isalnum() or c in "-_." for c in key):
        raise APIError(400, "invalid_idempotency_key", "Idempotency-Key chỉ gồm chữ, số, dấu -, _ hoặc .; tối đa 100 ký tự.")
    return customer, items, fingerprint, key


def existing_order(row, fingerprint):
    if row["request_hash"] != fingerprint:
        raise APIError(409, "idempotency_conflict", "Mã yêu cầu đã được dùng cho một đơn hàng khác.")
    return result(200, {"order": public(row), "replayed": True})


def public(row):
    return {k: v for k, v in row.items() if k not in ("request_hash", "idempotency_key")}


def create(event):
    customer, items, fingerprint, key = order_input(event)
    with connect() as conn:
        prior = conn.execute("SELECT * FROM orders WHERE idempotency_key=%s", (key,)).fetchone()
    if prior:
        return existing_order(prior, fingerprint)
    snapshot = []
    try:
        for item in items:
            product = upstream("product-service", "/products/" + item["product_id"])["product"]
            if product.get("active") is not True:
                raise APIError(400, "product_unavailable", "Một sản phẩm đã ngừng bán. Vui lòng kiểm tra giỏ hàng.")
            price = product["price_vnd"]
            if type(price) is not int or not 0 <= price <= 1_000_000_000:
                raise ValueError("Invalid product price")
            snapshot.append({**item, "product_name": product["name"], "unit_price_vnd": price})
        calculated = upstream("total-calculator", "/calculate", {"items": snapshot})
        expected = sum(item["quantity"] * item["unit_price_vnd"] for item in snapshot)
        if type(calculated.get("total_vnd")) is not int or calculated["total_vnd"] != expected:
            raise ValueError("Invalid calculated total")
    except (KeyError, TypeError, ValueError):
        raise APIError(502, "upstream_error", "Service phụ thuộc trả dữ liệu không hợp lệ. Chưa tạo đơn hàng.") from None
    for item in snapshot:
        item["line_total_vnd"] = item["quantity"] * item["unit_price_vnd"]
    with connect() as conn:
        row = conn.execute("""INSERT INTO orders(id,customer_name,phone,address,note,items,total_vnd,
            idempotency_key,request_hash) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (idempotency_key) DO NOTHING RETURNING *""",
            (str(uuid.uuid4()), customer["name"], customer["phone"], customer["address"], customer["note"],
             Jsonb(snapshot), expected, key, fingerprint)).fetchone()
        if row is None:
            prior = conn.execute("SELECT * FROM orders WHERE idempotency_key=%s", (key,)).fetchone()
            return existing_order(prior, fingerprint)
    LOGGER.info("Order created: %s", row["id"])
    return result(201, {"order": public(row), "replayed": False})


@api
def handle(event, context):
    path, method = route(event)
    if path == "/health":
        return health("order-service", True) if method == "GET" else method_not_allowed("GET")
    if path in ("/", "/orders"):
        if method == "POST":
            return create(event)
        if method == "GET":
            with connect() as conn:
                rows = conn.execute("SELECT * FROM orders ORDER BY created_at DESC,id LIMIT 200").fetchall()
            return result(200, {"orders": [public(row) for row in rows]})
        return method_not_allowed("GET, POST")
    parts = path.strip("/").split("/")
    if len(parts) in (2, 3) and parts[0] == "orders":
        oid = identifier(parts[1])
        if len(parts) == 2:
            if method != "GET":
                return method_not_allowed("GET")
            with connect() as conn:
                row = conn.execute("SELECT * FROM orders WHERE id=%s", (oid,)).fetchone()
        elif parts[2] == "cancel":
            if method != "POST":
                return method_not_allowed("POST")
            with connect() as conn:
                row = conn.execute("""UPDATE orders SET status='cancelled',updated_at=CURRENT_TIMESTAMP
                    WHERE id=%s AND status='pending' RETURNING *""", (oid,)).fetchone()
                if row is None:
                    exists = conn.execute("SELECT id FROM orders WHERE id=%s", (oid,)).fetchone()
                    if exists:
                        raise APIError(409, "invalid_order_status", "Chỉ có thể hủy đơn đang chờ xử lý.")
        else:
            not_found()
        if row is None:
            not_found()
        return result(200, {"order": public(row)})
    not_found()

