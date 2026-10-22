SET ROLE order_app;
CREATE TABLE orders (
    id UUID PRIMARY KEY,
    customer_name VARCHAR(120) NOT NULL,
    phone VARCHAR(30) NOT NULL,
    address VARCHAR(500) NOT NULL,
    note VARCHAR(500) NOT NULL DEFAULT '',
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','cancelled')),
    items JSONB NOT NULL CHECK (jsonb_typeof(items) = 'array'),
    total_vnd BIGINT NOT NULL CHECK (total_vnd >= 0),
    idempotency_key VARCHAR(100) NOT NULL UNIQUE,
    request_hash CHAR(64) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX orders_created_at_idx ON orders(created_at DESC);

