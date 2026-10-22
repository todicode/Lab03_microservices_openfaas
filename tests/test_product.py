import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import requests
from services import common, product_service

def event(data=None, method="POST", path="/", raw=None, content_type="application/json", headers=None):
    return SimpleNamespace(path=path, method=method, query={}, headers={"Content-Type": content_type, **(headers or {})},
                           body=raw if raw is not None else json.dumps(data).encode("utf-8"))

class ProductTests(unittest.TestCase):
    def test_product_validation(self):
            valid = {"name": "  Sổ Việt  ", "price_vnd": 1000, "category": "notebooks"}
            self.assertEqual(product_service.validate(valid)["name"], "Sổ Việt")
            for overrides in ({"name": ""}, {"name": "a" * 121}, {"price_vnd": True},
                              {"price_vnd": -1}, {"category": []}, {"active": "false"}):
                with self.subTest(overrides=overrides), self.assertRaises(common.APIError):
                    product_service.validate({**valid, **overrides})

    def test_invalid_uuid(self):
            self.assertEqual(product_service.handle(event(method="GET", path="/products/not-an-id"), None)["statusCode"], 400)
