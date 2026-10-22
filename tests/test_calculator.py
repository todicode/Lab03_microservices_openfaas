import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import requests
from services import common, total_calculator

def event(data=None, method="POST", path="/", raw=None, content_type="application/json", headers=None):
    return SimpleNamespace(path=path, method=method, query={}, headers={"Content-Type": content_type, **(headers or {})},
                           body=raw if raw is not None else json.dumps(data).encode("utf-8"))

class CalculatorTests(unittest.TestCase):
    def test_exact_integer_money(self):
        res = total_calculator.handle(event({"items": [
            {"unit_price_vnd": 129000, "quantity": 2}, {"unit_price_vnd": 35000, "quantity": 3}]}), None)
        self.assertEqual(res["statusCode"], 200)
        self.assertEqual(res["body"]["total_vnd"], 363000)
        self.assertEqual(res["body"]["items"][1]["line_total_vnd"], 105000)

    def test_invalid_items(self):
        for items in ([], None, "bad", [1], [{}], [{"unit_price_vnd": 1, "quantity": True}],
                      [{"unit_price_vnd": -1, "quantity": 1}], [{"unit_price_vnd": 1.1, "quantity": 1}],
                      [{"unit_price_vnd": 1, "quantity": 100}], [{}] * 51):
            with self.subTest(items=items):
                self.assertEqual(total_calculator.handle(event({"items": items}), None)["statusCode"], 400)

    def test_free_product(self):
        self.assertEqual(total_calculator.handle(event({"items": [
            {"unit_price_vnd": 0, "quantity": 1}]}), None)["body"]["total_vnd"], 0)

    def test_http_contract(self):
        for method, path, status in (("GET", "/health", 200), ("GET", "/calculate", 405),
                                     ("POST", "/missing", 404)):
            with self.subTest(method=method, path=path):
                self.assertEqual(total_calculator.handle(event(method=method, path=path), None)["statusCode"], status)

class InputTests(unittest.TestCase):
    def test_bad_json(self):
            for raw in (b"", b"{bad", b"\xff", b"[" * 2000):
                with self.subTest(raw=raw[:10]):
                    self.assertEqual(total_calculator.handle(event(raw=raw), None)["statusCode"], 400)

    def test_json_object_required(self):
            for data in (None, [], 1, True, "hello"):
                with self.subTest(data=data):
                    self.assertEqual(total_calculator.handle(event(data), None)["statusCode"], 400)

    def test_media_type_and_body_limit(self):
            self.assertEqual(total_calculator.handle(event({}, content_type="text/plain"), None)["statusCode"], 415)
            self.assertEqual(total_calculator.handle(event(raw=b" " * 65537), None)["statusCode"], 413)
