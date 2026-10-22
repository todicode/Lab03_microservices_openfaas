from pathlib import Path
import secrets

root = Path(__file__).resolve().parents[1]
target = root / ".env"
if target.exists():
    print(".env already exists; kept existing credentials.")
else:
    target.write_text("".join(f"{key}={secrets.token_hex(20)}\n" for key in
                             ("POSTGRES_PASSWORD", "PRODUCT_DB_PASSWORD", "ORDER_DB_PASSWORD")), encoding="utf-8")
    print("Created .env with separate random database passwords. Do not commit this file.")

