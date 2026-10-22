"""HTTP integration checks against real PostgreSQL and three running services."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import sys
import time
import uuid

import requests

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--base", default="http://127.0.0.1:8082")
parser.add_argument("--output", default="evidence/local-api.json")
args = parser.parse_args()
checks = []
base = args.base.rstrip("/")


def check(name, condition):
    checks.append({"name": name, "passed": bool(condition)})
    print(("PASS " if condition else "FAIL ") + name, flush=True)
    if not condition:
        raise AssertionError(name)


def request(service, path, method="GET", data=None, **kwargs):
    return requests.request(method, f"{base}/function/{service}{path}", json=data, timeout=45, **kwargs)


product_id = None
try:
    for service in ("product-service", "order-service", "total-calculator"):
        res = request(service, "/health")
        check(service + " healthy", res.status_code == 200 and res.json()["status"] == "ok")
    products = request("product-service", "/products").json()["products"]
    check("Seed products available", len(products) >= 6)
    values = {"name": "Kiểm thử " + str(uuid.uuid4())[:8], "description": "Tiếng Việt & <script> text",
              "category": "notebooks", "price_vnd": 12345, "active": True}
    res = request("product-service", "/products", "POST", values)
    check("Create product", res.status_code == 201)
    product_id = res.json()["product"]["id"]
    check("Read product", request("product-service", "/products/" + product_id).json()["product"]["price_vnd"] == 12345)
    search = request("product-service", "/products", params={"q": values["name"]})
    check("Search product", any(p["id"] == product_id for p in search.json()["products"]))
    values["price_vnd"] = 15000
    check("Update product", request("product-service", "/products/" + product_id, "PUT", values).status_code == 200)
    bad = request("product-service", "/products", "POST", {**values, "price_vnd": True})
    check("Reject invalid price", bad.status_code == 400)
    calc = request("total-calculator", "/calculate", "POST",
                   {"items": [{"unit_price_vnd": 15000, "quantity": 2}]}).json()
    check("Calculator exact VND total", calc["total_vnd"] == 30000)
    order_payload = {"customer_name": "Khách kiểm thử", "phone": "0900000000", "address": "Địa chỉ kiểm thử",
                     "items": [{"product_id": product_id, "quantity": 2, "unit_price_vnd": 1}], "total_vnd": 1}
    key = str(uuid.uuid4())
    def submit():
        return request("order-service", "/orders", "POST", order_payload, headers={"Idempotency-Key": key})
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(lambda _: submit(), range(2)))
    check("Concurrent retry creates exactly one order", sorted(r.status_code for r in responses) == [200, 201])
    orders = [r.json()["order"] for r in responses]
    order_id = orders[0]["id"]
    check("Concurrent responses share order ID", orders[1]["id"] == order_id)
    check("Server ignores client price", orders[0]["total_vnd"] == 30000)
    check("Idempotency replay", submit().status_code == 200)
    changed = {**order_payload, "customer_name": "Different"}
    check("Reject reused key with changed payload",
          request("order-service", "/orders", "POST", changed, headers={"Idempotency-Key": key}).status_code == 409)
    values["price_vnd"] = 99000
    request("product-service", "/products/" + product_id, "PUT", values)
    snapshot = request("order-service", "/orders/" + order_id).json()["order"]
    check("Order preserves purchase price", snapshot["items"][0]["unit_price_vnd"] == 15000 and snapshot["total_vnd"] == 30000)
    check("Order appears in list", any(o["id"] == order_id for o in request("order-service", "/orders").json()["orders"]))
    check("Cancel pending order", request("order-service", "/orders/" + order_id + "/cancel", "POST").json()["order"]["status"] == "cancelled")
    check("Reject second cancellation", request("order-service", "/orders/" + order_id + "/cancel", "POST").status_code == 409)
    check("Deactivate product", request("product-service", "/products/" + product_id, "DELETE").status_code == 200)
    check("Inactive product hidden", all(p["id"] != product_id for p in request("product-service", "/products").json()["products"]))
    check("Reject ordering inactive product", request("order-service", "/orders", "POST", order_payload).status_code == 400)
    invalid = requests.post(base + "/function/total-calculator/calculate", data="{oops", headers={"Content-Type": "application/json"}, timeout=10)
    check("Reject malformed JSON", invalid.status_code == 400)
    check("Unknown path returns 404", request("order-service", "/missing").status_code == 404)
    check("Unsupported method returns 405", request("total-calculator", "/calculate", "GET").status_code == 405)
finally:
    if product_id:
        try:
            request("product-service", "/products/" + product_id, "DELETE")
        except requests.RequestException:
            pass
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"base_url": base, "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                                "checks": checks, "passed": sum(c["passed"] for c in checks),
                                "total": len(checks)}, ensure_ascii=False, indent=2), encoding="utf-8")
