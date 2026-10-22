"""Local-only failure/recovery tests. Temporarily stops this lab's containers."""
import json
from pathlib import Path
import subprocess
import time
import uuid

import requests

ROOT = Path(__file__).resolve().parents[1]
BASE = "http://127.0.0.1:8082/function/"
checks = []


def compose(*args, expected=0):
    run = subprocess.run(["docker","compose",*args], cwd=ROOT, capture_output=True, text=True)
    if run.returncode != expected:
        raise RuntimeError("Docker Compose command failed: " + run.stderr[-500:])
    return run


def check(name, condition):
    checks.append({"name":name,"passed":bool(condition)})
    print(("PASS " if condition else "FAIL ") + name, flush=True)
    if not condition:
        raise AssertionError(name)


def wait_healthy(service):
    for attempt in range(30):
        try:
            if requests.get(BASE + service + "/health", timeout=5).status_code == 200:
                return
        except requests.RequestException:
            pass
        time.sleep(1)
    raise RuntimeError(service + " did not recover")


try:
    before = len(requests.get(BASE + "order-service/orders",timeout=10).json()["orders"])
    compose("stop","total-calculator")
    try:
        data = {"customer_name":"Khách kiểm thử lỗi","phone":"0900000000","address":"Địa chỉ giả lập",
                "items":[{"product_id":"10000000-0000-4000-8000-000000000001","quantity":1}]}
        res = requests.post(BASE + "order-service/orders",json=data,
                            headers={"Idempotency-Key":str(uuid.uuid4())},timeout=15)
        check("Unavailable calculator returns upstream error",res.status_code in (502, 504))
        after = len(requests.get(BASE + "order-service/orders",timeout=10).json()["orders"])
        check("Upstream failure does not persist an order",before == after)
    finally:
        compose("start","total-calculator")
        wait_healthy("total-calculator")
    check("Calculator recovers after restart",True)
    compose("stop","postgres")
    try:
        check("Database failure returns 503",
              requests.get(BASE + "product-service/health",timeout=10).status_code == 503)
    finally:
        compose("start","postgres")
        wait_healthy("product-service")
        wait_healthy("order-service")
    restored = len(requests.get(BASE + "order-service/orders",timeout=10).json()["orders"])
    check("Orders survive PostgreSQL restart",restored == before)
    for role, password, other in (("product_app","PRODUCT_DB_PASSWORD","order_db"),
                                   ("order_app","ORDER_DB_PASSWORD","product_db")):
        command = 'PGPASSWORD="$' + password + '" psql -h 127.0.0.1 -U ' + role + ' -d ' + other + ' -c "SELECT 1"'
        run = subprocess.run(["docker","compose","exec","-T","postgres","sh","-c",command],
                             cwd=ROOT,capture_output=True,text=True)
        check(role + " cannot connect to " + other, run.returncode != 0 and "permission denied" in run.stderr)
finally:
    target = ROOT / "evidence" / "local-resilience.json"
    target.parent.mkdir(exist_ok=True)
    target.write_text(json.dumps({"checks":checks,"passed":sum(c["passed"] for c in checks),
                                  "total":len(checks)},ensure_ascii=False,indent=2),encoding="utf-8")
