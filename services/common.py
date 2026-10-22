"""Small shared HTTP/validation helpers; no shared database access across services."""
import functools
import json
import logging
import os
import uuid
from pathlib import Path

import psycopg
from psycopg.rows import dict_row

LOGGER = logging.getLogger(__name__)
MAX_BODY = 65_536


class APIError(Exception):
    def __init__(self, status, code, message):
        self.status, self.code, self.message = status, code, message
        super().__init__(message)


def result(status, data, headers=None):
    return {"statusCode": status, "body": data,
            "headers": {"Content-Type": "application/json; charset=utf-8",
                        "Cache-Control": "no-store", **(headers or {})}}


def api(fn):
    @functools.wraps(fn)
    def wrapped(event, context):
        try:
            return fn(event, context)
        except APIError as exc:
            return result(exc.status, {"error": {"code": exc.code, "message": exc.message}})
        except psycopg.Error:
            LOGGER.warning("Database operation failed", exc_info=False)
            return result(503, {"error": {"code": "database_unavailable",
                                         "message": "Dữ liệu tạm thời chưa sẵn sàng. Vui lòng thử lại."}})
    return wrapped


def header(event, name, default=""):
    return next((str(v) for k, v in event.headers.items() if k.lower() == name.lower()), default)


def body(event):
    if header(event, "Content-Type").split(";", 1)[0].strip().lower() != "application/json":
        raise APIError(415, "unsupported_media_type", "Cần gửi Content-Type: application/json.")
    raw = event.body
    if not isinstance(raw, (str, bytes)):
        raise APIError(400, "invalid_json", "Nội dung phải là JSON UTF-8.")
    if len(raw if isinstance(raw, bytes) else raw.encode("utf-8")) > MAX_BODY:
        raise APIError(413, "payload_too_large", "Nội dung vượt quá 64 KiB.")
    try:
        data = json.loads(raw)
    except (ValueError, UnicodeError, RecursionError):
        raise APIError(400, "invalid_json", "JSON không hợp lệ.") from None
    if not isinstance(data, dict):
        raise APIError(400, "invalid_payload", "Nội dung JSON phải là một object.")
    return data


def text(data, key, limit, required=True):
    value = data.get(key, "")
    if not isinstance(value, str) or len(value.strip()) > limit or (required and not value.strip()):
        raise APIError(400, "invalid_" + key, f"{key}: chuỗi {'không rỗng, ' if required else ''}tối đa {limit} ký tự.")
    return value.strip()


def integer(value, name, low=1, high=1_000_000_000):
    if type(value) is not int or not low <= value <= high:
        raise APIError(400, "invalid_" + name, f"{name}: số nguyên từ {low} đến {high}.")
    return value


def identifier(value):
    try:
        return str(uuid.UUID(str(value)))
    except (ValueError, TypeError, AttributeError):
        raise APIError(400, "invalid_id", "Mã định danh phải là UUID hợp lệ.") from None


def route(event):
    return (event.path or "/").rstrip("/") or "/", event.method.upper()


def method_not_allowed(allowed):
    return result(405, {"error": {"code": "method_not_allowed", "message": "Phương thức không được hỗ trợ."}},
                  {"Allow": allowed})


def not_found():
    raise APIError(404, "not_found", "Không tìm thấy dữ liệu hoặc đường dẫn.")


def secret(name):
    path = Path("/var/openfaas/secrets") / name
    return path.read_text(encoding="utf-8").strip() if path.is_file() else ""


def connect():
    # Each container receives only its own database connection string.
    dsn = os.environ.get("DATABASE_URL") or secret(os.environ.get("DATABASE_SECRET", "database-url"))
    if not dsn:
        raise APIError(503, "database_unavailable", "Chưa cấu hình kết nối dữ liệu.")
    return psycopg.connect(dsn, connect_timeout=3, row_factory=dict_row,
                          options="-c statement_timeout=5000")


def health(service, database=False):
    if database:
        with connect() as conn:
            conn.execute("SELECT 1")
    return result(200, {"status": "ok", "service": service})

