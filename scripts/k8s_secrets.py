"""Apply secret manifests through stdin without printing credentials."""
import argparse
import base64
import json
from pathlib import Path
import subprocess

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--profile", default="lab03-openfaas")
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
values = dict(line.split("=", 1) for line in (root / ".env").read_text(encoding="utf-8-sig").splitlines()
              if line.strip() and not line.startswith("#") and "=" in line)
required = ("POSTGRES_PASSWORD", "PRODUCT_DB_PASSWORD", "ORDER_DB_PASSWORD")
if any(not values.get(key) for key in required):
    raise SystemExit("Run python scripts/setup_env.py before deployment.")
def apply(name, namespace, data):
    manifest = {"apiVersion":"v1", "kind":"Secret", "type":"Opaque",
                "metadata":{"name":name,"namespace":namespace},
                "data":{k:base64.b64encode(v.encode()).decode() for k,v in data.items()}}
    subprocess.run(["kubectl","--context",args.profile,"apply","-f","-"],
                   input=json.dumps(manifest).encode(), check=True)
apply("lab03-db-credentials", "lab03-data", {key:values[key] for key in required})
for service, role, database, variable in (
    ("product","product_app","product_db","PRODUCT_DB_PASSWORD"),
    ("order","order_app","order_db","ORDER_DB_PASSWORD")):
    from urllib.parse import quote
    dsn = f"postgresql://{role}:{quote(values[variable],safe='')}@postgres.lab03-data.svc.cluster.local:5432/{database}"
    apply(service + "-database-url", "openfaas-fn", {service + "-database-url":dsn})
