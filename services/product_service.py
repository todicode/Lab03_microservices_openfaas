import uuid

from .common import (APIError, api, body, connect, health, identifier, integer,
                     method_not_allowed, not_found, result, route, text)

CATEGORIES = {"notebooks", "writing", "desk", "accessories"}


def validate(data):
    category = data.get("category", "accessories")
    if not isinstance(category, str) or category not in CATEGORIES:
        raise APIError(400, "invalid_category", "Danh mục sản phẩm không hợp lệ.")
    active = data.get("active", True)
    if type(active) is not bool:
        raise APIError(400, "invalid_active", "active phải là boolean.")
    return {"name": text(data, "name", 120), "description": text(data, "description", 1000, False),
            "category": category, "price_vnd": integer(data.get("price_vnd"), "price_vnd", 0),
            "active": active}


@api
def handle(event, context):
    path, method = route(event)
    if path == "/health":
        return health("product-service", True) if method == "GET" else method_not_allowed("GET")
    if path in ("/", "/products"):
        if method == "GET":
            query = event.query or {}
            include_inactive = query.get("include_inactive") == "true"
            search = str(query.get("q", ""))[:120].strip()
            with connect() as conn:
                # strpos treats user search literally, including % and _.
                rows = conn.execute("""SELECT * FROM products
                    WHERE (%s OR active) AND (%s = '' OR strpos(lower(name), lower(%s)) > 0)
                    ORDER BY created_at, id LIMIT 200""", (include_inactive, search, search)).fetchall()
            return result(200, {"products": rows})
        if method == "POST":
            values = validate(body(event))
            values["id"] = str(uuid.uuid4())
            with connect() as conn:
                row = conn.execute("""INSERT INTO products(id,name,description,category,price_vnd,active)
                    VALUES (%(id)s,%(name)s,%(description)s,%(category)s,%(price_vnd)s,%(active)s)
                    RETURNING *""", values).fetchone()
            return result(201, {"product": row})
        return method_not_allowed("GET, POST")
    parts = path.strip("/").split("/")
    if len(parts) == 2 and parts[0] == "products":
        pid = identifier(parts[1])
        if method == "GET":
            with connect() as conn:
                row = conn.execute("SELECT * FROM products WHERE id=%s", (pid,)).fetchone()
        elif method == "PUT":
            values = validate(body(event))
            values["id"] = pid
            with connect() as conn:
                row = conn.execute("""UPDATE products SET name=%(name)s,description=%(description)s,
                    category=%(category)s,price_vnd=%(price_vnd)s,active=%(active)s,
                    updated_at=CURRENT_TIMESTAMP WHERE id=%(id)s RETURNING *""", values).fetchone()
        elif method == "DELETE":
            with connect() as conn:
                row = conn.execute("""UPDATE products SET active=false,updated_at=CURRENT_TIMESTAMP
                    WHERE id=%s RETURNING *""", (pid,)).fetchone()
        else:
            return method_not_allowed("GET, PUT, DELETE")
        if row is None:
            not_found()
        return result(200, {"product": row})
    not_found()

