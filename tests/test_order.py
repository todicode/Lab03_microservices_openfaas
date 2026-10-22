import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import requests
from services import common, order_service

def event(data=None, method="POST", path="/", raw=None, content_type="application/json", headers=None):
    return SimpleNamespace(path=path, method=method, query={}, headers={"Content-Type": content_type, **(headers or {})},
                           body=raw if raw is not None else json.dumps(data).encode("utf-8"))

class OrderTests(unittest.TestCase):
    def order(self, **kwargs):
        return {"customer_name": "Test", "phone": "0900000000", "address": "Test address",
                "items": [{"product_id": "10000000-0000-4000-8000-000000000001", "quantity": 2}], **kwargs}

    def test_merge_duplicate_lines(self):
        data = self.order()
        data["items"] *= 2
        customer, items, fingerprint, key = order_service.order_input(event(data))
        self.assertEqual(items[0]["quantity"], 4)
        self.assertEqual(len(fingerprint), 64)

    def test_reject_duplicate_quantity_overflow(self):
        data = self.order()
        data["items"][0]["quantity"] = 99
        data["items"] *= 2
        with self.assertRaises(common.APIError):
            order_service.order_input(event(data))

    def test_client_price_not_used(self):
        original = event(self.order())
        tampered = event(self.order(total_vnd=1, price_vnd=1))
        self.assertEqual(order_service.order_input(original)[2], order_service.order_input(tampered)[2])

    def test_idempotency_validation(self):
        for key in ("bad key", "x" * 101, "đơn"):
            with self.subTest(key=key), self.assertRaises(common.APIError):
                order_service.order_input(event(self.order(), headers={"Idempotency-Key": key}))

    def test_upstream_failures(self):
        for exc, status in ((requests.Timeout(), 504), (requests.ConnectionError(), 502)):
            with self.subTest(status=status), patch.object(order_service.requests, "request", side_effect=exc):
                with self.assertRaises(common.APIError) as raised:
                    order_service.upstream("product-service", "/products")
                self.assertEqual(raised.exception.status, status)

    def test_replay_conflict(self):
        with self.assertRaises(common.APIError) as raised:
            order_service.existing_order({"request_hash": "one"}, "two")
        self.assertEqual(raised.exception.status, 409)
