#!/bin/sh
set -eu
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
  --set=product_password="$PRODUCT_DB_PASSWORD" --set=order_password="$ORDER_DB_PASSWORD" <<'SQL'
CREATE USER product_app WITH PASSWORD :'product_password';
CREATE USER order_app WITH PASSWORD :'order_password';
CREATE DATABASE product_db OWNER product_app;
CREATE DATABASE order_db OWNER order_app;
REVOKE CONNECT ON DATABASE product_db FROM PUBLIC;
REVOKE CONNECT ON DATABASE order_db FROM PUBLIC;
GRANT CONNECT ON DATABASE product_db TO product_app;
GRANT CONNECT ON DATABASE order_db TO order_app;
SQL
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname product_db -f /schemas/products.sql
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname order_db -f /schemas/orders.sql

