from .common import (APIError, api, body, health, integer, method_not_allowed,
                     not_found, result, route)


@api
def handle(event, context):
    path, method = route(event)
    if path == "/health":
        return health("total-calculator") if method == "GET" else method_not_allowed("GET")
    if path not in ("/", "/calculate"):
        not_found()
    if method != "POST":
        return method_not_allowed("POST")
    items = body(event).get("items")
    if not isinstance(items, list) or not 1 <= len(items) <= 50:
        raise APIError(400, "invalid_items", "Đơn hàng cần từ 1 đến 50 dòng sản phẩm.")
    lines = []
    for item in items:
        if not isinstance(item, dict):
            raise APIError(400, "invalid_items", "Mỗi dòng sản phẩm phải là object.")
        price = integer(item.get("unit_price_vnd"), "unit_price_vnd", 0)
        quantity = integer(item.get("quantity"), "quantity", 1, 99)
        lines.append({"unit_price_vnd": price, "quantity": quantity, "line_total_vnd": price * quantity})
    return result(200, {"currency": "VND", "items": lines,
                        "total_vnd": sum(line["line_total_vnd"] for line in lines)})

